"""
Supervisor Agent

The Supervisor Agent provides oversight and governance for Primary Agent decisions.
It reviews decisions for quality, compliance, and appropriateness without directly
interacting with customers.

Uses LLM for nuanced tone and compliance evaluation.
Escalation rules and safety decisions remain deterministic.
Fails safely with conservative decisions when uncertain.
"""

import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from pydantic import BaseModel, Field, ValidationError

from app.agents.base import (
    AgentInput,
    AgentOutput,
    BaseAgent,
    ConfidenceReport,
)
from app.agents.prompts import (
    SUPERVISOR_AGENT_SYSTEM_PROMPT,
    build_supervisor_prompt,
)
from app.core.json_utils import extract_json_from_llm_response
from app.core.llm import (
    CompletionRequest,
    CompletionStatus,
    GenerationConfig,
    LLMClient,
    ResponseFormat,
)
from app.core.models import (
    AgentType,
    ConfidenceLevel,
    DecisionType,
    EmotionalState,
    IntentCategory,
)

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Supervisor-Specific Models
# -----------------------------------------------------------------------------

class RiskLevel(str, Enum):
    """Risk levels identified during review."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceStatus(str, Enum):
    """Compliance check results."""
    COMPLIANT = "compliant"
    WARNING = "warning"
    VIOLATION = "violation"


class ReviewFlag(str, Enum):
    """Flags that can be raised during review."""
    CONFIDENCE_TOO_HIGH = "confidence_too_high"
    CONFIDENCE_TOO_LOW = "confidence_too_low"
    TONE_MISMATCH = "tone_mismatch"
    INTENT_MISMATCH = "intent_mismatch"
    EMOTION_UNADDRESSED = "emotion_unaddressed"
    SENSITIVE_TOPIC = "sensitive_topic"
    POLICY_CONCERN = "policy_concern"
    QUALITY_ISSUE = "quality_issue"
    ESCALATION_RECOMMENDED = "escalation_recommended"


class SupervisorReview(BaseModel):
    """
    Structured output from supervisor review.
    
    Contains assessment of primary agent decision including
    quality, compliance, and any recommended adjustments.
    """
    review_id: str = Field(default_factory=lambda: str(uuid4()))
    decision_id: str = Field(description="ID of reviewed decision")
    interaction_id: str = Field(description="Associated interaction")
    
    # Review outcome
    approved: bool = Field(description="Whether decision is approved")
    
    # Quality assessment
    quality_score: float = Field(ge=0.0, le=1.0)
    tone_appropriate: bool = Field(default=True)
    response_relevant: bool = Field(default=True)
    
    # Compliance
    compliance_status: ComplianceStatus = Field(default=ComplianceStatus.COMPLIANT)
    compliance_notes: List[str] = Field(default_factory=list)
    
    # Risk assessment
    risk_level: RiskLevel = Field(default=RiskLevel.NONE)
    risk_factors: List[str] = Field(default_factory=list)
    
    # Confidence adjustment
    original_confidence: float = Field(description="Primary agent's confidence")
    adjusted_confidence: float = Field(description="Confidence after review")
    confidence_adjustment_reason: Optional[str] = Field(default=None)
    
    # Flags
    flags: List[ReviewFlag] = Field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list)
    requires_escalation_review: bool = Field(default=False)
    
    # Reasoning
    reasoning: List[str] = Field(default_factory=list)
    
    # Timing
    reviewed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# -----------------------------------------------------------------------------
# LLM Output Schema
# -----------------------------------------------------------------------------

class LLMReviewResult(BaseModel):
    """Structured output from LLM review."""
    
    approved: bool = Field(default=False)  # Conservative default
    quality_score: float = Field(default=0.5, ge=0.0, le=1.0)
    compliance_status: str = Field(default="warning")
    risk_level: str = Field(default="medium")
    tone_appropriate: bool = Field(default=False)  # Conservative default
    adjusted_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    flags: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    reasoning: List[str] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# Review Configuration (DETERMINISTIC - Never Overridden)
# -----------------------------------------------------------------------------

# Sensitive topics requiring extra scrutiny - ALWAYS triggers review
SENSITIVE_TOPICS: Set[str] = {
    "legal", "lawsuit", "attorney", "lawyer", "discrimination",
    "harassment", "threat", "suicide", "self-harm", "death",
    "fraud", "scam", "police", "emergency", "medical",
}

# Prohibited phrases in responses - ALWAYS violation
PROHIBITED_PHRASES: Set[str] = {
    "guarantee", "promise", "definitely", "always", "never",
    "100%", "absolutely certain", "no way", "impossible",
}

# High-risk intent categories - ALWAYS increases risk
HIGH_RISK_INTENTS: Set[IntentCategory] = {
    IntentCategory.COMPLAINT,
    IntentCategory.CANCELLATION,
}

# Emotions requiring careful handling - ALWAYS checked
HIGH_ATTENTION_EMOTIONS: Set[EmotionalState] = {
    EmotionalState.ANGRY,
    EmotionalState.FRUSTRATED,
    EmotionalState.ANXIOUS,
}

# Expected emotional acknowledgment phrases
EMOTIONAL_ACKNOWLEDGMENT_PHRASES: Dict[EmotionalState, List[str]] = {
    EmotionalState.FRUSTRATED: ["understand", "frustrating", "apologize"],
    EmotionalState.ANGRY: ["sorry", "apologize", "understand"],
    EmotionalState.ANXIOUS: ["understand", "urgent", "help", "priority"],
    EmotionalState.CONFUSED: ["clarify", "explain", "help"],
}


class SupervisorAgent(BaseAgent):
    """
    Supervisor Agent for AI governance.
    
    Responsible for:
    - Reviewing Primary Agent decisions
    - Assessing response quality and tone (LLM-assisted)
    - Checking compliance with policies (hybrid)
    - Adjusting confidence scores when warranted
    - Flagging risks and uncertainties
    
    Safety guarantees (NEVER overridden by LLM):
    - Sensitive topic detection is deterministic
    - Prohibited phrase detection is deterministic
    - Critical risk assessment is deterministic
    - Escalation triggers are deterministic
    
    Does NOT:
    - Interact directly with customers
    - Make final escalation decisions
    - Generate customer-facing responses
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        agent_id: Optional[str] = None,
    ):
        """
        Initialize the Supervisor Agent.
        
        Args:
            llm_client: Optional LLM client for nuanced evaluation.
                        If None, uses deterministic fallback logic.
            agent_id: Optional agent identifier.
        """
        super().__init__(agent_id=agent_id)
        self._llm_client = llm_client
        self._use_llm = llm_client is not None

    @property
    def agent_type(self) -> AgentType:
        """Return SUPERVISOR agent type."""
        return AgentType.SUPERVISOR

    async def process(self, input_data: AgentInput) -> AgentOutput:
        """
        Process is not the primary interface for SupervisorAgent.
        Use review_decision() instead for reviewing Primary Agent outputs.
        """
        confidence = await self.assess_confidence(
            input_data,
            DecisionType.DEFER,
        )
        
        return AgentOutput(
            decision_id=uuid4(),
            interaction_id=input_data.interaction_id,
            agent_type=self.agent_type,
            decision_type=DecisionType.DEFER,
            decision_summary="Supervisor review - no direct customer interaction",
            response_content=None,
            detected_intent=input_data.suggested_intent,
            detected_emotion=input_data.suggested_emotion,
            confidence=confidence,
            reasoning=["Supervisor agent does not process customer messages directly"],
            requires_followup=False,
            recommended_actions=["Route to Primary Agent for customer interaction"],
            escalation_target=None,
            context_updates={},
            processed_at=datetime.now(timezone.utc),
            processing_duration_ms=0,
        )

    async def assess_confidence(
        self,
        input_data: AgentInput,
        preliminary_decision: DecisionType,
    ) -> ConfidenceReport:
        """Assess confidence for supervisor operations."""
        return ConfidenceReport(
            overall_score=0.9,
            level=ConfidenceLevel.HIGH,
            intent_confidence=0.9,
            emotion_confidence=0.9,
            context_confidence=0.9,
            factors=["Supervisor review uses deterministic safety rules"],
            concerns=[],
            meets_autonomous_threshold=True,
            requires_supervision=False,
            requires_escalation=False,
        )

    async def review_decision(
        self,
        primary_output: AgentOutput,
        original_input: AgentInput,
    ) -> SupervisorReview:
        """
        Review a decision made by the Primary Agent.
        
        Combines LLM-based nuanced evaluation with deterministic safety rules.
        Safety rules ALWAYS take precedence over LLM suggestions.
        
        Args:
            primary_output: The output from Primary Agent to review.
            original_input: The original customer input.
            
        Returns:
            SupervisorReview with assessment and recommendations.
        """
        reasoning = ["Initiating supervisor review of Primary Agent decision"]
        flags: List[ReviewFlag] = []
        recommendations: List[str] = []
        risk_factors: List[str] = []
        compliance_notes: List[str] = []
        
        # =====================================================================
        # PHASE 1: Deterministic Safety Checks (NEVER bypassed)
        # =====================================================================
        
        # 1a. Sensitive topic detection (deterministic)
        has_sensitive, sensitive_topics = self._detect_sensitive_topics(
            original_input.content,
        )
        if has_sensitive:
            flags.append(ReviewFlag.SENSITIVE_TOPIC)
            risk_factors.append(f"Sensitive topics detected: {', '.join(sensitive_topics)}")
            reasoning.append("SAFETY: Sensitive topic detected - mandatory review")
        
        # 1b. Prohibited phrases check (deterministic)
        has_prohibited, prohibited_found = self._check_prohibited_phrases(
            primary_output.response_content or "",
        )
        if has_prohibited:
            flags.append(ReviewFlag.POLICY_CONCERN)
            compliance_notes.append(f"Prohibited phrases: {', '.join(prohibited_found)}")
            reasoning.append("SAFETY: Prohibited phrases detected - compliance violation")
        
        # 1c. Deterministic risk assessment
        base_risk_level, base_risk_factors = self._assess_risk_deterministic(
            primary_output,
            original_input,
        )
        risk_factors.extend(base_risk_factors)
        
        # 1d. Emotional acknowledgment check (deterministic)
        emotion_addressed, emotion_issues = self._check_emotional_acknowledgment(
            primary_output,
            original_input,
        )
        if not emotion_addressed:
            flags.append(ReviewFlag.EMOTION_UNADDRESSED)
            recommendations.extend(emotion_issues)
        
        # =====================================================================
        # PHASE 2: LLM-Assisted Nuanced Evaluation (with fallback)
        # =====================================================================
        
        llm_result = await self._evaluate_with_llm(
            primary_output,
            original_input,
        )
        
        # Track if we used fallback
        used_fallback = llm_result.get("used_fallback", True)
        if used_fallback:
            reasoning.append("Using deterministic fallback evaluation")
        else:
            reasoning.append("LLM-assisted evaluation completed")
        
        # Extract LLM results
        llm_quality_score = llm_result["quality_score"]
        llm_tone_appropriate = llm_result["tone_appropriate"]
        llm_compliance_status = llm_result["compliance_status"]
        llm_recommendations = llm_result["recommendations"]
        llm_reasoning = llm_result["reasoning"]
        
        # =====================================================================
        # PHASE 3: Merge Results (Safety Rules Override LLM)
        # =====================================================================
        
        # Quality score: use LLM but cap if safety issues
        quality_score = llm_quality_score
        if has_prohibited:
            quality_score = min(quality_score, 0.4)  # Penalize for violations
        if has_sensitive and not emotion_addressed:
            quality_score = min(quality_score, 0.5)
        
        quality_issues = []
        if quality_score < 0.7:
            flags.append(ReviewFlag.QUALITY_ISSUE)
            quality_issues = self._assess_quality_fallback(primary_output, original_input)
            recommendations.extend(quality_issues)
        
        reasoning.append(f"Quality assessment: {quality_score:.2f}")
        
        # Tone: use LLM but override if deterministic check failed
        tone_appropriate = llm_tone_appropriate and emotion_addressed
        if not tone_appropriate:
            flags.append(ReviewFlag.TONE_MISMATCH)
        reasoning.append(f"Tone assessment: {'appropriate' if tone_appropriate else 'concerns'}")
        
        # Compliance: MOST RESTRICTIVE of LLM and deterministic
        if has_prohibited:
            compliance_status = ComplianceStatus.VIOLATION
        elif llm_compliance_status == ComplianceStatus.VIOLATION:
            compliance_status = ComplianceStatus.VIOLATION
        elif llm_compliance_status == ComplianceStatus.WARNING or has_sensitive:
            compliance_status = ComplianceStatus.WARNING
        else:
            compliance_status = ComplianceStatus.COMPLIANT
        
        compliance_notes.extend(llm_result.get("compliance_notes", []))
        reasoning.append(f"Compliance status: {compliance_status.value}")
        
        # Risk level: HIGHEST of LLM and deterministic
        llm_risk = self._parse_risk_level(llm_result.get("risk_level", "medium"))
        risk_level = self._max_risk(base_risk_level, llm_risk)
        
        # Force high risk for sensitive topics
        if has_sensitive:
            risk_level = self._max_risk(risk_level, RiskLevel.HIGH)
        
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            flags.append(ReviewFlag.ESCALATION_RECOMMENDED)
        
        reasoning.append(f"Risk level: {risk_level.value}")
        
        # Recommendations: merge all
        recommendations.extend(llm_recommendations)
        
        # Reasoning: include LLM reasoning
        reasoning.extend([f"LLM: {r}" for r in llm_reasoning[:5]])
        
        # =====================================================================
        # PHASE 4: Confidence Adjustment (Deterministic)
        # =====================================================================
        
        adjusted_confidence, adjustment_reason = self._validate_confidence(
            primary_output,
            flags,
            risk_level,
            quality_score,
            compliance_status,
        )
        
        if adjusted_confidence != primary_output.confidence.overall_score:
            if adjusted_confidence > primary_output.confidence.overall_score:
                flags.append(ReviewFlag.CONFIDENCE_TOO_LOW)
            else:
                flags.append(ReviewFlag.CONFIDENCE_TOO_HIGH)
            reasoning.append(
                f"Confidence adjusted: {primary_output.confidence.overall_score:.2f} → {adjusted_confidence:.2f}"
            )
        
        # =====================================================================
        # PHASE 5: Final Approval Decision (Conservative)
        # =====================================================================
        
        approved = self._determine_approval(
            quality_score,
            tone_appropriate,
            compliance_status,
            risk_level,
            flags,
            adjusted_confidence,
        )
        
        reasoning.append(f"Final decision: {'approved' if approved else 'NOT APPROVED'}")
        
        if not approved:
            recommendations.insert(0, "Decision requires revision before delivery")
        
        if risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.append("Consider human oversight for this interaction")
        
        return SupervisorReview(
            decision_id=str(primary_output.decision_id),
            interaction_id=str(primary_output.interaction_id),
            approved=approved,
            quality_score=quality_score,
            tone_appropriate=tone_appropriate,
            response_relevant=quality_score >= 0.6,
            compliance_status=compliance_status,
            compliance_notes=compliance_notes,
            risk_level=risk_level,
            risk_factors=risk_factors,
            original_confidence=primary_output.confidence.overall_score,
            adjusted_confidence=adjusted_confidence,
            confidence_adjustment_reason=adjustment_reason,
            flags=flags,
            recommendations=recommendations,
            requires_escalation_review=risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL],
            reasoning=reasoning,
        )

    # =========================================================================
    # LLM-Assisted Evaluation
    # =========================================================================

    async def _evaluate_with_llm(
        self,
        primary_output: AgentOutput,
        original_input: AgentInput,
    ) -> Dict[str, Any]:
        """
        Perform LLM-based nuanced evaluation with safe fallback.
        
        Returns conservative defaults if LLM fails.
        """
        if not self._use_llm or self._llm_client is None:
            return self._fallback_evaluation(primary_output, original_input)
        
        try:
            # Build prompt
            primary_reasoning = "\n".join(primary_output.reasoning[:10])
            user_prompt = build_supervisor_prompt(
                customer_message=original_input.content,
                detected_intent=primary_output.detected_intent.value if primary_output.detected_intent else "unknown",
                detected_emotion=primary_output.detected_emotion.value if primary_output.detected_emotion else "neutral",
                original_confidence=primary_output.confidence.overall_score,
                generated_response=primary_output.response_content or "",
                primary_reasoning=primary_reasoning,
                channel=original_input.metadata.get("channel", "chat"),
                turn_count=original_input.context.turn_count if original_input.context else 1,
                escalation_count=0,
            )
            
            # Create completion request
            request = CompletionRequest(
                user_prompt=user_prompt,
                system_prompt=SUPERVISOR_AGENT_SYSTEM_PROMPT,
                config=GenerationConfig(
                    temperature=0.2,  # Low temperature for consistency
                    max_tokens=1024,  # Increased for complete JSON responses
                    response_format=ResponseFormat.JSON,
                ),
            )
            
            # Execute LLM call
            response = await self._llm_client.complete(request)
            
            if response.status != CompletionStatus.SUCCESS or not response.content:
                logger.warning(
                    f"Supervisor LLM call failed: {response.error_message}"
                )
                return self._fallback_evaluation(primary_output, original_input)
            
            # Parse result
            result = self._parse_llm_review(response.content)
            if result is None:
                logger.warning("Failed to parse supervisor LLM output")
                return self._fallback_evaluation(primary_output, original_input)
            
            return result
            
        except Exception as e:
            logger.error(f"Supervisor LLM evaluation failed: {e}")
            return self._fallback_evaluation(primary_output, original_input)

    def _normalize_string_list(self, items: List[Any]) -> List[str]:
        """
        Normalize a list to ensure all items are strings.
        
        Ollama sometimes returns nested objects like:
        {"step": "quality_assessment", "details": "..."}
        
        This extracts text from such structures.
        """
        result = []
        for item in items:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                # Extract meaningful text from dict
                if 'details' in item:
                    result.append(str(item['details']))
                elif 'description' in item:
                    result.append(str(item['description']))
                elif 'step' in item and 'details' in item:
                    result.append(f"{item['step']}: {item['details']}")
                elif 'type' in item and 'suggestion' in item:
                    result.append(str(item['suggestion']))
                else:
                    # Fallback: join all values
                    values = [str(v) for v in item.values() if v]
                    if values:
                        result.append(" - ".join(values))
            else:
                result.append(str(item))
        return result

    def _parse_llm_review(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Safely parse LLM JSON output.
        
        Returns None if parsing fails - triggers fallback.
        Handles Ollama returning nested objects instead of strings.
        """
        try:
            # Use robust JSON extraction utility
            data = extract_json_from_llm_response(content)
            if data is None:
                logger.warning(f"JSON parse error in supervisor: Could not extract JSON from LLM response")
                return None
            
            # Pre-process data to handle Ollama's nested object responses
            if 'recommendations' in data and isinstance(data['recommendations'], list):
                data['recommendations'] = self._normalize_string_list(data['recommendations'])
            if 'reasoning' in data and isinstance(data['reasoning'], list):
                data['reasoning'] = self._normalize_string_list(data['reasoning'])
            if 'flags' in data and isinstance(data['flags'], list):
                data['flags'] = self._normalize_string_list(data['flags'])
            
            result = LLMReviewResult.model_validate(data)
            
            return {
                "quality_score": max(0.0, min(1.0, result.quality_score)),
                "tone_appropriate": result.tone_appropriate,
                "compliance_status": self._parse_compliance_status(result.compliance_status),
                "risk_level": result.risk_level,
                "recommendations": result.recommendations[:5],
                "reasoning": result.reasoning[:5],
                "compliance_notes": [],
                "used_fallback": False,
            }
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error in supervisor: {e}")
            return None
        except ValidationError as e:
            logger.warning(f"Validation error in supervisor: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected parse error in supervisor: {e}")
            return None

    def _fallback_evaluation(
        self,
        primary_output: AgentOutput,
        original_input: AgentInput,
    ) -> Dict[str, Any]:
        """
        Deterministic fallback evaluation when LLM unavailable.
        
        Uses conservative defaults and rule-based checks.
        """
        # Quality assessment
        quality_score = 0.7  # Start neutral
        quality_issues = self._assess_quality_fallback(primary_output, original_input)
        quality_score -= len(quality_issues) * 0.1
        quality_score = max(0.3, min(1.0, quality_score))
        
        # Tone check
        tone_appropriate = self._assess_tone_fallback(primary_output)
        
        # Compliance
        compliance_status = ComplianceStatus.COMPLIANT
        if primary_output.confidence.level in [ConfidenceLevel.LOW, ConfidenceLevel.UNCERTAIN]:
            compliance_status = ComplianceStatus.WARNING
        
        return {
            "quality_score": quality_score,
            "tone_appropriate": tone_appropriate,
            "compliance_status": compliance_status,
            "risk_level": "medium",  # Conservative default
            "recommendations": quality_issues,
            "reasoning": ["Using deterministic fallback evaluation"],
            "compliance_notes": [],
            "used_fallback": True,
        }

    # =========================================================================
    # Deterministic Safety Checks (Never Overridden)
    # =========================================================================

    def _detect_sensitive_topics(
        self,
        content: str,
    ) -> tuple[bool, List[str]]:
        """Detect sensitive topics - ALWAYS applied."""
        content_lower = content.lower()
        found = [topic for topic in SENSITIVE_TOPICS if topic in content_lower]
        return len(found) > 0, found

    def _check_prohibited_phrases(
        self,
        response: str,
    ) -> tuple[bool, List[str]]:
        """Check for prohibited phrases - ALWAYS violation."""
        response_lower = response.lower()
        found = [phrase for phrase in PROHIBITED_PHRASES if phrase in response_lower]
        return len(found) > 0, found

    def _assess_risk_deterministic(
        self,
        output: AgentOutput,
        input_data: AgentInput,
    ) -> tuple[RiskLevel, List[str]]:
        """
        Deterministic risk assessment based on hard rules.
        
        This is ALWAYS applied regardless of LLM evaluation.
        """
        risk_factors = []
        risk_score = 0
        
        # High-risk intents
        if output.detected_intent in HIGH_RISK_INTENTS:
            risk_score += 2
            risk_factors.append(f"High-risk intent: {output.detected_intent.value}")
        
        # High-attention emotions
        if output.detected_emotion in HIGH_ATTENTION_EMOTIONS:
            risk_score += 1
            risk_factors.append(f"Elevated emotion: {output.detected_emotion.value}")
        
        # Angry + complaint = critical
        if (output.detected_emotion == EmotionalState.ANGRY and 
            output.detected_intent == IntentCategory.COMPLAINT):
            risk_score += 2
            risk_factors.append("Angry customer with complaint - escalation likely needed")
        
        # Low confidence
        if output.confidence.level in [ConfidenceLevel.LOW, ConfidenceLevel.UNCERTAIN]:
            risk_score += 1
            risk_factors.append("Low confidence in primary decision")
        
        # Unknown intent
        if output.detected_intent == IntentCategory.UNKNOWN:
            risk_score += 1
            risk_factors.append("Intent could not be determined")
        
        # Determine level
        if risk_score >= 4:
            level = RiskLevel.CRITICAL
        elif risk_score >= 3:
            level = RiskLevel.HIGH
        elif risk_score >= 2:
            level = RiskLevel.MEDIUM
        elif risk_score >= 1:
            level = RiskLevel.LOW
        else:
            level = RiskLevel.NONE
        
        return level, risk_factors

    def _check_emotional_acknowledgment(
        self,
        output: AgentOutput,
        input_data: AgentInput,
    ) -> tuple[bool, List[str]]:
        """Verify emotional acknowledgment - ALWAYS checked."""
        issues = []
        
        if not output.response_content:
            return True, []
        
        emotion = output.detected_emotion
        if emotion not in HIGH_ATTENTION_EMOTIONS:
            return True, []
        
        response_lower = output.response_content.lower()
        expected_phrases = EMOTIONAL_ACKNOWLEDGMENT_PHRASES.get(emotion, [])
        
        acknowledged = any(phrase in response_lower for phrase in expected_phrases)
        
        if not acknowledged:
            issues.append(
                f"Customer appears {emotion.value} but response lacks acknowledgment"
            )
        
        return acknowledged, issues

    # =========================================================================
    # Fallback Quality/Tone Checks
    # =========================================================================

    def _assess_quality_fallback(
        self,
        output: AgentOutput,
        input_data: AgentInput,
    ) -> List[str]:
        """Deterministic quality issues check."""
        issues = []
        
        if not output.response_content:
            issues.append("No response content generated")
        elif len(output.response_content) < 20:
            issues.append("Response too brief")
        elif len(output.response_content) > 1000:
            issues.append("Response may be too verbose")
        
        if not output.reasoning:
            issues.append("No reasoning provided for decision")
        elif len(output.reasoning) < 2:
            issues.append("Reasoning chain incomplete")
        
        if output.detected_intent == IntentCategory.UNKNOWN:
            issues.append("Intent could not be determined")
        
        return issues

    def _assess_tone_fallback(
        self,
        output: AgentOutput,
    ) -> bool:
        """Deterministic tone check."""
        if not output.response_content:
            return True
        
        response_lower = output.response_content.lower()
        
        # Check tone matches emotion
        if output.detected_emotion == EmotionalState.ANGRY:
            if "sorry" not in response_lower and "apologize" not in response_lower:
                return False
        
        if output.detected_emotion == EmotionalState.ANXIOUS:
            if "urgent" not in response_lower and "priority" not in response_lower:
                return False
        
        return True

    # =========================================================================
    # Confidence and Approval (Deterministic)
    # =========================================================================

    def _validate_confidence(
        self,
        output: AgentOutput,
        flags: List[ReviewFlag],
        risk_level: RiskLevel,
        quality_score: float,
        compliance_status: ComplianceStatus,
    ) -> tuple[float, Optional[str]]:
        """
        Validate and adjust confidence - DETERMINISTIC.
        
        Confidence adjustments follow strict rules.
        """
        original = output.confidence.overall_score
        adjusted = original
        reason = None
        
        # ALWAYS lower confidence for critical risk
        if risk_level == RiskLevel.CRITICAL:
            adjusted = min(adjusted, 0.3)
            reason = "Critical risk - requires human oversight"
        elif risk_level == RiskLevel.HIGH:
            adjusted = min(adjusted, 0.5)
            reason = "High risk - reduced confidence"
        elif risk_level == RiskLevel.MEDIUM and original > 0.7:
            adjusted = 0.65
            reason = "Medium risk with high confidence - adjusted for caution"
        
        # ALWAYS lower for compliance violation
        if compliance_status == ComplianceStatus.VIOLATION:
            adjusted = min(adjusted, 0.3)
            reason = "Compliance violation detected"
        elif compliance_status == ComplianceStatus.WARNING and adjusted > 0.7:
            adjusted = 0.65
            reason = "Compliance warning - moderate confidence"
        
        # Lower for quality issues
        if quality_score < 0.5 and adjusted > 0.5:
            adjusted = min(adjusted, 0.5)
            reason = "Quality issues detected"
        
        # Lower for unaddressed emotions
        if ReviewFlag.EMOTION_UNADDRESSED in flags and adjusted > 0.6:
            adjusted = min(adjusted, 0.6)
            reason = "Emotional needs not addressed"
        
        # Only raise confidence for clearly safe cases
        if (risk_level == RiskLevel.NONE and 
            len(flags) == 0 and 
            original < 0.6 and
            output.detected_intent != IntentCategory.UNKNOWN and
            compliance_status == ComplianceStatus.COMPLIANT):
            adjusted = max(adjusted, 0.7)
            reason = "Low-risk case with clear intent - confidence raised"
        
        return round(adjusted, 3), reason

    def _determine_approval(
        self,
        quality_score: float,
        tone_appropriate: bool,
        compliance_status: ComplianceStatus,
        risk_level: RiskLevel,
        flags: List[ReviewFlag],
        adjusted_confidence: float,
    ) -> bool:
        """
        Determine approval - CONSERVATIVE by default.
        
        When in doubt, DO NOT APPROVE.
        """
        # NEVER approve compliance violations
        if compliance_status == ComplianceStatus.VIOLATION:
            return False
        
        # NEVER approve critical risk
        if risk_level == RiskLevel.CRITICAL:
            return False
        
        # NEVER approve very low quality
        if quality_score < 0.4:
            return False
        
        # NEVER approve very low confidence
        if adjusted_confidence < 0.4:
            return False
        
        # Policy concerns block approval
        if ReviewFlag.POLICY_CONCERN in flags:
            return False
        
        # High risk with low confidence blocks approval
        if risk_level == RiskLevel.HIGH and adjusted_confidence < 0.6:
            return False
        
        # Sensitive topics with unaddressed emotions blocks approval
        if (ReviewFlag.SENSITIVE_TOPIC in flags and 
            ReviewFlag.EMOTION_UNADDRESSED in flags):
            return False
        
        # Medium quality + poor tone = cautious rejection
        if quality_score < 0.6 and not tone_appropriate:
            return False
        
        return True

    # =========================================================================
    # Helpers
    # =========================================================================

    def _parse_compliance_status(self, status_str: str) -> ComplianceStatus:
        """Parse compliance status string to enum."""
        status_map = {
            "compliant": ComplianceStatus.COMPLIANT,
            "warning": ComplianceStatus.WARNING,
            "violation": ComplianceStatus.VIOLATION,
        }
        return status_map.get(status_str.lower(), ComplianceStatus.WARNING)

    def _parse_risk_level(self, risk_str: str) -> RiskLevel:
        """Parse risk level string to enum."""
        risk_map = {
            "none": RiskLevel.NONE,
            "low": RiskLevel.LOW,
            "medium": RiskLevel.MEDIUM,
            "high": RiskLevel.HIGH,
            "critical": RiskLevel.CRITICAL,
        }
        return risk_map.get(risk_str.lower(), RiskLevel.MEDIUM)

    def _max_risk(self, r1: RiskLevel, r2: RiskLevel) -> RiskLevel:
        """Return the higher of two risk levels."""
        order = [RiskLevel.NONE, RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        return order[max(order.index(r1), order.index(r2))]

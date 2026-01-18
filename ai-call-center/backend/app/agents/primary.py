"""
Primary Interaction Agent

The Primary Agent is the first point of contact for customer interactions.
It handles intent detection, emotion assessment, and proposes resolutions
for standard customer inquiries.

Uses LLM for understanding and response drafting, with deterministic
confidence scoring and fallback logic.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field, ValidationError

from app.agents.base import (
    AgentInput,
    AgentOutput,
    BaseAgent,
    ConfidenceReport,
)
from app.agents.prompts import (
    PRIMARY_AGENT_SYSTEM_PROMPT,
    build_primary_prompt,
    format_conversation_history,
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
    ConversationContext,
    DecisionType,
    EmotionalState,
    IntentCategory,
)
from app.services.knowledge_base import get_knowledge_base

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# LLM Output Schema
# -----------------------------------------------------------------------------

class LLMAnalysisResult(BaseModel):
    """Structured output from LLM analysis."""
    
    intent: str = Field(default="unknown")
    emotion: str = Field(default="neutral")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    response: str = Field(default="")
    reasoning: List[str] = Field(default_factory=list)
    requires_clarification: bool = Field(default=False)
    suggested_actions: List[str] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# Fallback Constants (Used when LLM fails)
# -----------------------------------------------------------------------------

INTENT_KEYWORDS: Dict[IntentCategory, List[str]] = {
    IntentCategory.BILLING_INQUIRY: [
        "bill", "invoice", "charge", "payment", "statement", "balance", "due", "fee"
    ],
    IntentCategory.TECHNICAL_SUPPORT: [
        "error", "broken", "not working", "bug", "crash", "slow", "issue", "problem", "fix"
    ],
    IntentCategory.ACCOUNT_MANAGEMENT: [
        "account", "password", "login", "profile", "settings", "update", "change"
    ],
    IntentCategory.PRODUCT_INFORMATION: [
        "product", "feature", "how does", "what is", "explain", "information", "details"
    ],
    IntentCategory.COMPLAINT: [
        "terrible", "awful", "worst", "unacceptable", "disappointed", "complain", "sue"
    ],
    IntentCategory.FEEDBACK: [
        "feedback", "suggestion", "improve", "recommend", "love", "great", "amazing"
    ],
    IntentCategory.ORDER_STATUS: [
        "order", "shipping", "delivery", "track", "where is", "status", "arrived"
    ],
    IntentCategory.CANCELLATION: [
        "cancel", "refund", "return", "stop", "end subscription", "unsubscribe"
    ],
    IntentCategory.GENERAL_INQUIRY: [
        "help", "question", "wondering", "curious", "info"
    ],
    IntentCategory.FEEDBACK: [
        "feedback", "suggestion", "improve", "recommend", "love", "great", "amazing",
        "happy", "satisfied", "that's all", "no more questions"
    ],
}

EMOTION_KEYWORDS: Dict[EmotionalState, List[str]] = {
    EmotionalState.FRUSTRATED: [
        "frustrated", "annoying", "ridiculous", "again", "still", "keeps happening",
        "waste of time", "not working", "doesn't work", "useless", "terrible",
        "fed up", "sick of", "tired of", "for the third time", "repeated"
    ],
    EmotionalState.ANGRY: [
        "angry", "furious", "outraged", "unacceptable", "demand", "immediately",
        "lawsuit", "sue", "manager", "supervisor", "escalate", "ridiculous",
        "disgusting", "worst", "scam", "fraud", "liar", "lying"
    ],
    EmotionalState.CONFUSED: [
        "confused", "don't understand", "unclear", "lost", "what do you mean", "huh",
        "can you explain", "i'm not sure", "what does that mean", "sorry what",
        "don't get it", "makes no sense", "which one", "how do i"
    ],
    EmotionalState.ANXIOUS: [
        "worried", "concerned", "urgent", "asap", "emergency", "critical", "scared",
        "help me", "please help", "need this now", "can't wait", "right away",
        "time sensitive", "deadline", "desperately", "panic"
    ],
    EmotionalState.SATISFIED: [
        "thank you", "thanks", "great", "perfect", "excellent", "appreciate",
        "happy", "satisfied", "that works", "sounds good", "helpful", "wonderful",
        "that's all", "all good", "no more questions", "resolved", "awesome",
        "amazing", "good job", "well done", "very helpful", "problem solved",
        "that's exactly", "you've been great", "i'm happy", "i'm satisfied",
        "no further questions", "that answers my question", "thanks so much",
        "really appreciate", "you're the best", "fantastic", "love it"
    ],
}

# Phrases that indicate customer wants to end the call positively
CALL_END_POSITIVE = [
    "that's all i needed", "that's it", "nothing else", "i'm good",
    "you've answered everything", "that covers it", "we're done",
    "i think that's all", "no more questions", "all set", "good to go"
]

# Phrases indicating issue is not resolved
ISSUE_NOT_RESOLVED = [
    "still not working", "didn't help", "doesn't solve", "not what i asked",
    "you're not understanding", "that's not right", "wrong answer",
    "i already tried that", "already did that", "same problem"
]

FALLBACK_RESPONSES: Dict[IntentCategory, str] = {
    IntentCategory.BILLING_INQUIRY: (
        "I can help you with your billing inquiry. I've retrieved your account information "
        "and can provide details about your current balance, recent charges, or payment options."
    ),
    IntentCategory.TECHNICAL_SUPPORT: (
        "I understand you're experiencing a technical issue. Let me help troubleshoot this. "
        "Could you describe what's happening in more detail?"
    ),
    IntentCategory.ACCOUNT_MANAGEMENT: (
        "I can assist with your account management request. I have access to your account "
        "settings and can help you make the necessary changes."
    ),
    IntentCategory.PRODUCT_INFORMATION: (
        "I'd be happy to provide information about our products and services. "
        "What specific details would you like to know?"
    ),
    IntentCategory.COMPLAINT: (
        "I'm sorry to hear about your experience. Your feedback is important to us, "
        "and I want to ensure we address your concerns properly."
    ),
    IntentCategory.FEEDBACK: (
        "Thank you so much! I'm glad I could help you today. "
        "Is there anything else I can assist you with, or would you like me to close this call?"
    ),
    IntentCategory.ORDER_STATUS: (
        "I can check the status of your order. Let me retrieve the latest "
        "tracking information for you."
    ),
    IntentCategory.CANCELLATION: (
        "I understand you'd like to discuss cancellation. Before we proceed, "
        "I'd like to understand your reasons and see if there's anything we can do to help."
    ),
    IntentCategory.GENERAL_INQUIRY: (
        "Thank you for reaching out. I'm here to help. "
        "Could you tell me more about what you're looking for?"
    ),
    IntentCategory.UNKNOWN: (
        "Thank you for your message. I want to make sure I understand your request correctly. "
        "Could you provide a bit more detail about how I can assist you today?"
    ),
}


# -----------------------------------------------------------------------------
# Primary Agent Implementation
# -----------------------------------------------------------------------------

class PrimaryAgent(BaseAgent):
    """
    Primary Interaction Agent.
    
    Responsible for:
    - Initial customer greeting and engagement
    - Intent detection from customer messages (via LLM)
    - Emotional state assessment (via LLM)
    - Proposing resolutions for standard inquiries
    - Generating structured decisions with confidence scores
    
    Uses LLM for understanding and response drafting.
    Confidence scoring remains deterministic for consistency.
    Falls back to keyword-based logic if LLM fails.
    
    Does NOT handle:
    - Escalation decisions (deferred to Supervisor Agent)
    - Complex multi-step resolutions
    - Sensitive or high-risk scenarios
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        agent_id: Optional[str] = None,
    ):
        """
        Initialize the Primary Agent.
        
        Args:
            llm_client: Optional LLM client for AI-powered analysis.
                        If None, uses fallback keyword-based logic.
            agent_id: Optional agent identifier.
        """
        super().__init__(agent_id=agent_id)
        self._llm_client = llm_client
        self._use_llm = llm_client is not None

    @property
    def agent_type(self) -> AgentType:
        """Return PRIMARY agent type."""
        return AgentType.PRIMARY

    async def process(self, input_data: AgentInput) -> AgentOutput:
        """
        Process customer input and generate a response decision.
        
        Flow:
        1. Attempt LLM-based analysis (if client available)
        2. Fall back to keyword-based analysis if LLM fails
        3. Apply deterministic confidence scoring
        4. Package into structured output
        """
        start_time = datetime.now(timezone.utc)
        
        # Attempt LLM analysis with fallback
        analysis = await self._analyze_with_llm(input_data)
        
        # Extract results
        detected_intent = analysis["intent"]
        detected_emotion = analysis["emotion"]
        intent_confidence = analysis["intent_confidence"]
        emotion_confidence = analysis["emotion_confidence"]
        response_content = analysis["response"]
        llm_reasoning = analysis["reasoning"]
        intent_factors = analysis["intent_factors"]
        emotion_factors = analysis["emotion_factors"]
        used_fallback = analysis["used_fallback"]
        
        # Determine decision type (deterministic)
        decision_type = self._determine_decision_type(
            detected_intent,
            detected_emotion,
            input_data.context,
        )
        
        # Assess overall confidence (deterministic)
        confidence = await self.assess_confidence(
            input_data,
            decision_type,
            intent_confidence=intent_confidence,
            emotion_confidence=emotion_confidence,
            intent_factors=intent_factors,
            emotion_factors=emotion_factors,
            used_fallback=used_fallback,
        )
        
        # Build reasoning chain
        reasoning = self._build_reasoning(
            detected_intent,
            detected_emotion,
            decision_type,
            llm_reasoning,
            intent_factors,
            emotion_factors,
            used_fallback,
        )
        
        # Calculate processing time
        end_time = datetime.now(timezone.utc)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        return AgentOutput(
            decision_id=uuid4(),
            interaction_id=input_data.interaction_id,
            agent_type=self.agent_type,
            decision_type=decision_type,
            decision_summary=self._summarize_decision(decision_type, detected_intent),
            response_content=response_content,
            detected_intent=detected_intent,
            detected_emotion=detected_emotion,
            confidence=confidence,
            reasoning=reasoning,
            requires_followup=decision_type == DecisionType.CLARIFY,
            recommended_actions=self._get_recommended_actions(decision_type, detected_intent),
            escalation_target=None,
            context_updates={
                "last_intent": detected_intent.value if detected_intent else None,
                "last_emotion": detected_emotion.value if detected_emotion else None,
                "turn_processed": True,
                "used_llm": not used_fallback,
            },
            processed_at=end_time,
            processing_duration_ms=duration_ms,
        )

    async def _analyze_with_llm(self, input_data: AgentInput) -> Dict[str, Any]:
        """
        Perform LLM-based analysis with safe fallback.
        
        Returns a dictionary with analysis results regardless of
        whether LLM succeeded or fallback was used.
        """
        if not self._use_llm or self._llm_client is None:
            return self._fallback_analysis(input_data.content)
        
        try:
            # Build prompt with knowledge base context
            conversation_history = self._format_context_history(input_data.context)
            
            # Get knowledge base context for the customer message
            kb = get_knowledge_base()
            customer_id = input_data.metadata.get("customer_id") if input_data.metadata else None
            knowledge_context = kb.build_context_for_query(input_data.content, customer_id)
            
            user_prompt = build_primary_prompt(
                customer_message=input_data.content,
                channel=input_data.metadata.get("channel", "chat"),
                turn_count=input_data.context.turn_count if input_data.context else 1,
                previous_intent=input_data.suggested_intent.value if input_data.suggested_intent else "none",
                previous_emotion=input_data.suggested_emotion.value if input_data.suggested_emotion else "neutral",
                conversation_history=conversation_history,
                knowledge_context=knowledge_context if knowledge_context else "No specific knowledge base match found.",
            )
            
            # Create completion request
            request = CompletionRequest(
                user_prompt=user_prompt,
                system_prompt=PRIMARY_AGENT_SYSTEM_PROMPT,
                config=GenerationConfig(
                    temperature=0.3,  # Low temperature for consistency
                    max_tokens=1024,  # Increased for complete JSON responses
                    response_format=ResponseFormat.JSON,
                ),
            )
            
            # Execute LLM call
            response = await self._llm_client.complete(request)
            
            # Check for success
            if response.status != CompletionStatus.SUCCESS or not response.content:
                logger.warning(
                    f"LLM call failed with status {response.status}: {response.error_message}"
                )
                return self._fallback_analysis(input_data.content)
            
            # Parse structured output
            result = self._parse_llm_output(response.content)
            if result is None:
                logger.warning("Failed to parse LLM output, using fallback")
                return self._fallback_analysis(input_data.content)
            
            return result
            
        except Exception as e:
            logger.error(f"LLM analysis failed with exception: {e}")
            return self._fallback_analysis(input_data.content)

    def _parse_llm_output(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Safely parse LLM JSON output into structured result.
        
        Returns None if parsing fails.
        """
        try:
            # Use robust JSON extraction utility
            data = extract_json_from_llm_response(content)
            if data is None:
                logger.warning(f"JSON parse error: Could not extract JSON from LLM response")
                return None
            
            # Validate with Pydantic
            result = LLMAnalysisResult.model_validate(data)
            
            # Map string values to enums
            intent = self._parse_intent(result.intent)
            emotion = self._parse_emotion(result.emotion)
            
            # Validate confidence is within bounds
            llm_confidence = max(0.0, min(1.0, result.confidence))
            
            # Calculate separate confidence scores
            # LLM's self-reported confidence affects intent confidence
            intent_confidence = llm_confidence * 0.9  # Slight discount for LLM uncertainty
            emotion_confidence = llm_confidence * 0.85  # Emotions are harder to detect
            
            return {
                "intent": intent,
                "emotion": emotion,
                "intent_confidence": intent_confidence,
                "emotion_confidence": emotion_confidence,
                "response": result.response,
                "reasoning": result.reasoning,
                "intent_factors": [f"LLM detected intent: {result.intent}"],
                "emotion_factors": [f"LLM detected emotion: {result.emotion}"],
                "used_fallback": False,
            }
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}")
            return None
        except ValidationError as e:
            logger.warning(f"Validation error: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected parse error: {e}")
            return None

    def _parse_intent(self, intent_str: str) -> IntentCategory:
        """Parse intent string to IntentCategory enum."""
        intent_map = {
            "billing_inquiry": IntentCategory.BILLING_INQUIRY,
            "technical_support": IntentCategory.TECHNICAL_SUPPORT,
            "account_management": IntentCategory.ACCOUNT_MANAGEMENT,
            "product_information": IntentCategory.PRODUCT_INFORMATION,
            "complaint": IntentCategory.COMPLAINT,
            "feedback": IntentCategory.FEEDBACK,
            "order_status": IntentCategory.ORDER_STATUS,
            "cancellation": IntentCategory.CANCELLATION,
            "general_inquiry": IntentCategory.GENERAL_INQUIRY,
            "unknown": IntentCategory.UNKNOWN,
        }
        return intent_map.get(intent_str.lower(), IntentCategory.UNKNOWN)

    def _parse_emotion(self, emotion_str: str) -> EmotionalState:
        """Parse emotion string to EmotionalState enum."""
        emotion_map = {
            "neutral": EmotionalState.NEUTRAL,
            "satisfied": EmotionalState.SATISFIED,
            "frustrated": EmotionalState.FRUSTRATED,
            "confused": EmotionalState.CONFUSED,
            "urgent": EmotionalState.ANXIOUS,
            "anxious": EmotionalState.ANXIOUS,
            "angry": EmotionalState.ANGRY,
        }
        return emotion_map.get(emotion_str.lower(), EmotionalState.NEUTRAL)

    def _fallback_analysis(self, content: str) -> Dict[str, Any]:
        """
        Keyword-based fallback analysis when LLM is unavailable.
        
        Uses deterministic keyword matching for consistent behavior.
        """
        # Detect intent using keywords
        intent, intent_confidence, intent_factors = self._detect_intent_keywords(content)
        
        # Detect emotion using keywords
        emotion, emotion_confidence, emotion_factors = self._detect_emotion_keywords(content)
        
        # Generate response using templates
        response = self._generate_fallback_response(intent, emotion)
        
        return {
            "intent": intent,
            "emotion": emotion,
            "intent_confidence": intent_confidence,
            "emotion_confidence": emotion_confidence,
            "response": response,
            "reasoning": ["Using keyword-based fallback analysis"],
            "intent_factors": intent_factors,
            "emotion_factors": emotion_factors,
            "used_fallback": True,
        }

    def _detect_intent_keywords(
        self, content: str
    ) -> Tuple[IntentCategory, float, List[str]]:
        """Detect intent using keyword matching."""
        content_lower = content.lower()
        
        best_intent = IntentCategory.UNKNOWN
        best_score = 0.0
        best_matches: List[str] = []
        
        for intent, keywords in INTENT_KEYWORDS.items():
            matches = [kw for kw in keywords if kw in content_lower]
            if matches:
                score = min(0.85, 0.5 + (len(matches) * 0.12))
                if score > best_score:
                    best_score = score
                    best_intent = intent
                    best_matches = matches
        
        factors = []
        if best_matches:
            factors.append(f"Keywords matched: {', '.join(best_matches[:3])}")
        
        if best_intent == IntentCategory.UNKNOWN:
            best_score = 0.3
            factors.append("No strong intent indicators found")
        
        return best_intent, best_score, factors

    def _detect_emotion_keywords(
        self, content: str
    ) -> Tuple[EmotionalState, float, List[str]]:
        """Detect emotion using keyword matching with improved accuracy."""
        content_lower = content.lower()
        
        best_emotion = EmotionalState.NEUTRAL
        best_score = 0.6
        best_matches: List[str] = []
        
        # Check for positive call-ending phrases first (high confidence satisfaction)
        for phrase in CALL_END_POSITIVE:
            if phrase in content_lower:
                return EmotionalState.SATISFIED, 0.92, [f"Positive closing: '{phrase}'"]
        
        # Check for unresolved issue indicators (indicates frustration/need for escalation)
        unresolved_matches = [p for p in ISSUE_NOT_RESOLVED if p in content_lower]
        if unresolved_matches:
            return EmotionalState.FRUSTRATED, 0.85, [f"Issue unresolved: {unresolved_matches[0]}"]
        
        # Standard emotion keyword detection with weighted scoring
        for emotion, keywords in EMOTION_KEYWORDS.items():
            matches = [kw for kw in keywords if kw in content_lower]
            if matches:
                # Weight by number of matches and emotion severity
                base_score = 0.55
                match_bonus = len(matches) * 0.12
                
                # Boost score for clear positive signals
                if emotion == EmotionalState.SATISFIED:
                    # More matches = higher confidence in satisfaction
                    score = min(0.95, base_score + match_bonus + 0.15)
                elif emotion in [EmotionalState.ANGRY, EmotionalState.FRUSTRATED]:
                    # Negative emotions get priority detection
                    score = min(0.90, base_score + match_bonus + 0.10)
                else:
                    score = min(0.85, base_score + match_bonus)
                
                if score > best_score:
                    best_score = score
                    best_emotion = emotion
                    best_matches = matches
        
        factors = []
        if best_matches:
            factors.append(f"Emotion indicators: {', '.join(best_matches[:3])}")
        else:
            factors.append("No strong emotional indicators, assuming neutral")
        
        return best_emotion, best_score, factors

    def _generate_fallback_response(
        self,
        intent: IntentCategory,
        emotion: EmotionalState,
    ) -> str:
        """Generate response using fallback templates."""
        base_response = FALLBACK_RESPONSES.get(
            intent,
            FALLBACK_RESPONSES[IntentCategory.UNKNOWN]
        )
        
        emotional_prefix = ""
        if emotion == EmotionalState.FRUSTRATED:
            emotional_prefix = "I understand this situation is frustrating. "
        elif emotion == EmotionalState.ANGRY:
            emotional_prefix = "I sincerely apologize for any inconvenience. "
        elif emotion == EmotionalState.ANXIOUS:
            emotional_prefix = "I understand this is urgent for you. "
        elif emotion == EmotionalState.CONFUSED:
            emotional_prefix = "Let me help clarify this for you. "
        
        return emotional_prefix + base_response

    def _format_context_history(
        self, context: Optional[ConversationContext]
    ) -> str:
        """Format conversation context for prompt inclusion."""
        if context is None:
            return "No previous messages."
        
        # Simplified formatting - real implementation would use
        # actual message history from context store
        lines = []
        if context.key_topics:
            lines.append(f"Key topics discussed: {', '.join(context.key_topics)}")
        if context.unresolved_issues:
            lines.append(f"Unresolved issues: {', '.join(context.unresolved_issues)}")
        if context.intent_history:
            recent_intents = [i.value for i in context.intent_history[-3:]]
            lines.append(f"Recent intents: {', '.join(recent_intents)}")
        
        return "\n".join(lines) if lines else "No previous messages."

    async def assess_confidence(
        self,
        input_data: AgentInput,
        preliminary_decision: DecisionType,
        intent_confidence: float = 0.5,
        emotion_confidence: float = 0.5,
        intent_factors: Optional[List[str]] = None,
        emotion_factors: Optional[List[str]] = None,
        used_fallback: bool = False,
    ) -> ConfidenceReport:
        """
        Assess confidence in the decision.
        
        This is DETERMINISTIC - not influenced by LLM randomness.
        
        Factors:
        - Intent detection clarity
        - Emotion detection clarity  
        - Context availability
        - Message characteristics
        - Whether fallback was used (penalty)
        """
        intent_factors = intent_factors or []
        emotion_factors = emotion_factors or []
        
        # Calculate context confidence
        context_confidence = self._calculate_context_confidence(input_data.context)
        
        # Apply fallback penalty if applicable
        fallback_penalty = 0.15 if used_fallback else 0.0
        
        # Calculate overall score (weighted average with penalty)
        overall_score = (
            intent_confidence * 0.4 +
            emotion_confidence * 0.3 +
            context_confidence * 0.3
        ) - fallback_penalty
        
        # Boost confidence for satisfied customers (they're likely done)
        detected_emotion = input_data.context.emotion_history[-1] if (
            input_data.context and input_data.context.emotion_history
        ) else None
        
        if detected_emotion == EmotionalState.SATISFIED or emotion_confidence >= 0.85:
            overall_score = min(0.95, overall_score + 0.15)
        
        # Lower confidence if customer seems frustrated and issue persists
        if detected_emotion == EmotionalState.FRUSTRATED:
            overall_score = max(0.35, overall_score - 0.10)
        
        overall_score = max(0.0, min(1.0, overall_score))
        
        # Determine confidence level
        level = self._score_to_level(overall_score)
        
        # Compile factors and concerns
        factors = []
        concerns = []
        
        if intent_confidence >= 0.7:
            factors.append("Clear intent detected")
        elif intent_confidence < 0.5:
            concerns.append("Intent unclear or ambiguous")
        
        if emotion_confidence >= 0.7:
            factors.append("Customer emotional state identified")
        elif emotion_confidence < 0.5:
            concerns.append("Emotional state difficult to assess")
        
        if context_confidence >= 0.7:
            factors.append("Rich conversation context available")
        elif context_confidence < 0.5:
            concerns.append("Limited context for decision-making")
        
        if len(input_data.content) > 20:
            factors.append("Sufficient message length for analysis")
        else:
            concerns.append("Short message limits analysis depth")
        
        if used_fallback:
            concerns.append("Using fallback analysis (LLM unavailable)")
        
        factors.extend(intent_factors)
        factors.extend(emotion_factors)
        
        # Determine thresholds
        meets_autonomous = overall_score >= 0.7
        requires_supervision = 0.5 <= overall_score < 0.7
        requires_escalation = overall_score < 0.5
        
        return ConfidenceReport(
            overall_score=round(overall_score, 3),
            level=level,
            intent_confidence=round(intent_confidence, 3),
            emotion_confidence=round(emotion_confidence, 3),
            context_confidence=round(context_confidence, 3),
            factors=factors,
            concerns=concerns,
            meets_autonomous_threshold=meets_autonomous,
            requires_supervision=requires_supervision,
            requires_escalation=requires_escalation,
        )

    def _determine_decision_type(
        self,
        intent: IntentCategory,
        emotion: EmotionalState,
        context: Optional[ConversationContext],
    ) -> DecisionType:
        """Determine appropriate decision type (deterministic)."""
        if intent == IntentCategory.UNKNOWN:
            return DecisionType.CLARIFY
        
        if intent == IntentCategory.COMPLAINT:
            return DecisionType.DEFER
        
        return DecisionType.RESPOND

    def _calculate_context_confidence(
        self, context: Optional[ConversationContext]
    ) -> float:
        """Calculate confidence based on available context."""
        if context is None:
            return 0.4
        
        score = 0.5
        
        if context.turn_count > 0:
            score += min(0.2, context.turn_count * 0.05)
        
        if context.key_topics:
            score += 0.1
        
        if context.intent_history:
            score += 0.1
        
        return min(0.9, score)

    def _score_to_level(self, score: float) -> ConfidenceLevel:
        """Convert numeric score to confidence level."""
        if score >= 0.8:
            return ConfidenceLevel.HIGH
        elif score >= 0.6:
            return ConfidenceLevel.MEDIUM
        elif score >= 0.4:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.UNCERTAIN

    def _build_reasoning(
        self,
        intent: IntentCategory,
        emotion: EmotionalState,
        decision: DecisionType,
        llm_reasoning: List[str],
        intent_factors: List[str],
        emotion_factors: List[str],
        used_fallback: bool,
    ) -> List[str]:
        """Build explainable reasoning chain."""
        reasoning = [
            f"Analyzed customer message for intent and emotion",
            f"Analysis method: {'Fallback (keyword-based)' if used_fallback else 'LLM-powered'}",
            f"Detected intent: {intent.value}",
            f"Detected emotion: {emotion.value}",
        ]
        
        if llm_reasoning and not used_fallback:
            reasoning.append("LLM reasoning:")
            reasoning.extend([f"  - {r}" for r in llm_reasoning[:5]])
        
        reasoning.extend(intent_factors)
        reasoning.extend(emotion_factors)
        reasoning.append(f"Selected decision type: {decision.value}")
        
        return reasoning

    def _summarize_decision(
        self, decision: DecisionType, intent: IntentCategory
    ) -> str:
        """Generate human-readable decision summary."""
        summaries = {
            DecisionType.RESPOND: f"Responding to {intent.value.replace('_', ' ')} inquiry",
            DecisionType.CLARIFY: "Requesting clarification due to unclear intent",
            DecisionType.DEFER: f"Deferring {intent.value.replace('_', ' ')} for review",
        }
        return summaries.get(decision, "Processing customer request")

    def _get_recommended_actions(
        self, decision: DecisionType, intent: IntentCategory
    ) -> List[str]:
        """Get recommended follow-up actions."""
        actions = []
        
        if decision == DecisionType.CLARIFY:
            actions.append("Wait for customer clarification")
            actions.append("Prepare follow-up questions")
        elif decision == DecisionType.DEFER:
            actions.append("Notify supervisor for review")
        elif intent == IntentCategory.CANCELLATION:
            actions.append("Prepare retention offers")
        
        return actions

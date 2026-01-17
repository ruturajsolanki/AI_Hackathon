"""
Metrics Engine

In-memory analytics engine for tracking interaction metrics,
agent performance, and computed satisfaction scores.

All logic is deterministic and explainable.
"""

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.models import (
    AgentType,
    ChannelType,
    ConfidenceLevel,
    EmotionalState,
    IntentCategory,
)


# -----------------------------------------------------------------------------
# Metrics Models
# -----------------------------------------------------------------------------

class ResolutionType(str, Enum):
    """How an interaction was resolved."""
    AI_RESOLVED = "ai_resolved"
    HUMAN_ESCALATED = "human_escalated"
    ABANDONED = "abandoned"
    TRANSFERRED = "transferred"


class InteractionMetrics(BaseModel):
    """Metrics for a single interaction."""
    interaction_id: UUID
    channel: ChannelType
    
    # Timing
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Resolution
    resolution_type: Optional[ResolutionType] = None
    turn_count: int = 0
    escalation_count: int = 0
    
    # Classification
    primary_intent: Optional[IntentCategory] = None
    final_emotion: Optional[EmotionalState] = None
    
    # Confidence
    confidence_scores: List[float] = Field(default_factory=list)
    average_confidence: Optional[float] = None
    min_confidence: Optional[float] = None
    max_confidence: Optional[float] = None
    
    # Computed CSAT (1-5 scale)
    computed_csat: Optional[float] = None
    csat_factors: Dict[str, float] = Field(default_factory=dict)


class AggregatedMetrics(BaseModel):
    """Aggregated metrics across interactions."""
    period_start: datetime
    period_end: datetime
    
    # Volume
    total_interactions: int = 0
    interactions_by_channel: Dict[str, int] = Field(default_factory=dict)
    interactions_by_intent: Dict[str, int] = Field(default_factory=dict)
    
    # Resolution
    ai_resolved_count: int = 0
    human_escalated_count: int = 0
    abandoned_count: int = 0
    resolution_rate: float = 0.0  # AI resolved / total
    escalation_rate: float = 0.0  # Human escalated / total
    
    # Duration
    average_duration_seconds: float = 0.0
    min_duration_seconds: float = 0.0
    max_duration_seconds: float = 0.0
    
    # Confidence
    average_confidence: float = 0.0
    confidence_distribution: Dict[str, int] = Field(default_factory=dict)
    
    # CSAT
    average_csat: float = 0.0
    csat_distribution: Dict[str, int] = Field(default_factory=dict)
    
    # Trends
    turn_count_average: float = 0.0
    escalation_rate_trend: List[float] = Field(default_factory=list)


class AgentPerformanceMetrics(BaseModel):
    """Performance metrics for an agent type."""
    agent_type: AgentType
    
    # Volume
    decisions_made: int = 0
    
    # Confidence
    average_confidence: float = 0.0
    high_confidence_rate: float = 0.0
    low_confidence_rate: float = 0.0
    
    # Approval (for Primary Agent)
    approval_rate: Optional[float] = None
    override_rate: Optional[float] = None
    
    # Escalation (for Escalation Agent)
    escalation_decision_rate: Optional[float] = None


# -----------------------------------------------------------------------------
# CSAT Computation Logic
# -----------------------------------------------------------------------------

# Weight factors for CSAT computation (must sum to 1.0)
CSAT_WEIGHTS = {
    "resolution": 0.30,      # Was it resolved by AI?
    "confidence": 0.20,      # Agent confidence level
    "duration": 0.15,        # Interaction duration
    "turns": 0.15,           # Number of turns
    "emotion_trend": 0.20,   # Emotional trajectory
}

# Target thresholds for scoring
DURATION_THRESHOLDS = {
    "excellent": 120,   # Under 2 minutes
    "good": 300,        # Under 5 minutes
    "acceptable": 600,  # Under 10 minutes
}

TURN_THRESHOLDS = {
    "excellent": 3,
    "good": 5,
    "acceptable": 8,
}


def compute_csat(
    resolution_type: Optional[ResolutionType],
    average_confidence: Optional[float],
    duration_seconds: Optional[float],
    turn_count: int,
    emotion_history: List[EmotionalState],
) -> Tuple[float, Dict[str, float]]:
    """
    Compute simulated CSAT score based on interaction metrics.
    
    Returns a score from 1.0 to 5.0 and contributing factors.
    
    Scoring logic:
    - Resolution: AI resolved = 5, Human escalated = 3, Abandoned = 1
    - Confidence: Maps 0-1 to 1-5
    - Duration: Faster is better (5 for <2min, 1 for >10min)
    - Turns: Fewer is better (5 for <=3, 1 for >8)
    - Emotion: Improved = 5, Stable = 3, Worsened = 1
    """
    factors: Dict[str, float] = {}
    
    # Resolution factor (1-5)
    if resolution_type == ResolutionType.AI_RESOLVED:
        factors["resolution"] = 5.0
    elif resolution_type == ResolutionType.HUMAN_ESCALATED:
        factors["resolution"] = 3.0
    elif resolution_type == ResolutionType.TRANSFERRED:
        factors["resolution"] = 3.5
    else:  # Abandoned or None
        factors["resolution"] = 1.0
    
    # Confidence factor (1-5)
    if average_confidence is not None:
        factors["confidence"] = 1.0 + (average_confidence * 4.0)
    else:
        factors["confidence"] = 3.0  # Neutral
    
    # Duration factor (1-5)
    if duration_seconds is not None:
        if duration_seconds <= DURATION_THRESHOLDS["excellent"]:
            factors["duration"] = 5.0
        elif duration_seconds <= DURATION_THRESHOLDS["good"]:
            factors["duration"] = 4.0
        elif duration_seconds <= DURATION_THRESHOLDS["acceptable"]:
            factors["duration"] = 3.0
        else:
            factors["duration"] = max(1.0, 3.0 - (duration_seconds - 600) / 300)
    else:
        factors["duration"] = 3.0
    
    # Turn count factor (1-5)
    if turn_count <= TURN_THRESHOLDS["excellent"]:
        factors["turns"] = 5.0
    elif turn_count <= TURN_THRESHOLDS["good"]:
        factors["turns"] = 4.0
    elif turn_count <= TURN_THRESHOLDS["acceptable"]:
        factors["turns"] = 3.0
    else:
        factors["turns"] = max(1.0, 3.0 - (turn_count - 8) * 0.5)
    
    # Emotion trend factor (1-5)
    factors["emotion_trend"] = _compute_emotion_trend_score(emotion_history)
    
    # Compute weighted average
    csat = sum(
        factors.get(key, 3.0) * weight
        for key, weight in CSAT_WEIGHTS.items()
    )
    
    return round(csat, 2), factors


def _compute_emotion_trend_score(emotions: List[EmotionalState]) -> float:
    """
    Compute emotion trend score.
    
    Scoring:
    - Ended satisfied/neutral after frustration = 5.0 (improved)
    - Started and ended satisfied = 4.5
    - Stable neutral = 3.5
    - No change from negative = 2.0
    - Worsened to angry = 1.0
    """
    if not emotions:
        return 3.0
    
    # Emotion valence mapping
    valence = {
        EmotionalState.SATISFIED: 2,
        EmotionalState.NEUTRAL: 1,
        EmotionalState.CONFUSED: 0,
        EmotionalState.ANXIOUS: -1,
        EmotionalState.FRUSTRATED: -2,
        EmotionalState.ANGRY: -3,
    }
    
    first_emotion = emotions[0]
    last_emotion = emotions[-1]
    
    first_valence = valence.get(first_emotion, 0)
    last_valence = valence.get(last_emotion, 0)
    
    # Calculate trend
    trend = last_valence - first_valence
    
    if trend >= 2:
        return 5.0  # Significant improvement
    elif trend >= 1:
        return 4.0  # Improvement
    elif trend == 0:
        if last_valence >= 1:
            return 4.0  # Stable positive
        elif last_valence == 0:
            return 3.0  # Stable neutral
        else:
            return 2.0  # Stable negative
    elif trend >= -1:
        return 2.0  # Slight worsening
    else:
        return 1.0  # Significant worsening


# -----------------------------------------------------------------------------
# Metrics Engine
# -----------------------------------------------------------------------------

@dataclass
class MetricsEngine:
    """
    In-memory analytics engine for tracking and aggregating metrics.
    
    Responsibilities:
    - Tracking interaction duration and resolution
    - Recording agent confidence scores
    - Computing simulated CSAT scores
    - Providing aggregated metrics
    
    Does NOT:
    - Persist to external storage
    - Generate visualizations
    - Handle real-time streaming
    """
    
    # Storage
    _interactions: Dict[UUID, InteractionMetrics] = field(default_factory=dict)
    _agent_decisions: Dict[AgentType, List[Dict]] = field(
        default_factory=lambda: defaultdict(list)
    )
    _emotion_histories: Dict[UUID, List[EmotionalState]] = field(
        default_factory=lambda: defaultdict(list)
    )
    
    # Lock for concurrent access
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def start_interaction(
        self,
        interaction_id: UUID,
        channel: ChannelType,
        started_at: Optional[datetime] = None,
    ) -> InteractionMetrics:
        """
        Start tracking an interaction.
        
        Args:
            interaction_id: Unique interaction ID.
            channel: Communication channel.
            started_at: Start time (defaults to now).
            
        Returns:
            New InteractionMetrics instance.
        """
        async with self._lock:
            metrics = InteractionMetrics(
                interaction_id=interaction_id,
                channel=channel,
                started_at=started_at or datetime.now(timezone.utc),
            )
            self._interactions[interaction_id] = metrics
            return metrics

    async def record_turn(
        self,
        interaction_id: UUID,
        intent: Optional[IntentCategory] = None,
        emotion: Optional[EmotionalState] = None,
        confidence: Optional[float] = None,
        agent_type: AgentType = AgentType.PRIMARY,
    ) -> bool:
        """
        Record a conversation turn.
        
        Args:
            interaction_id: Target interaction.
            intent: Detected intent (if any).
            emotion: Detected emotion (if any).
            confidence: Agent confidence score.
            agent_type: Type of agent that processed.
            
        Returns:
            True if recorded, False if interaction not found.
        """
        async with self._lock:
            metrics = self._interactions.get(interaction_id)
            if not metrics:
                return False
            
            # Update turn count
            metrics.turn_count += 1
            
            # Update primary intent if not set
            if intent and not metrics.primary_intent:
                metrics.primary_intent = intent
            
            # Track emotion
            if emotion:
                metrics.final_emotion = emotion
                self._emotion_histories[interaction_id].append(emotion)
            
            # Track confidence
            if confidence is not None:
                metrics.confidence_scores.append(confidence)
            
            # Record agent decision
            self._agent_decisions[agent_type].append({
                "interaction_id": interaction_id,
                "confidence": confidence,
                "timestamp": datetime.now(timezone.utc),
            })
            
            return True

    async def record_escalation(
        self,
        interaction_id: UUID,
    ) -> bool:
        """
        Record an escalation event.
        
        Args:
            interaction_id: Target interaction.
            
        Returns:
            True if recorded, False if interaction not found.
        """
        async with self._lock:
            metrics = self._interactions.get(interaction_id)
            if not metrics:
                return False
            
            metrics.escalation_count += 1
            return True

    async def end_interaction(
        self,
        interaction_id: UUID,
        resolution_type: ResolutionType,
        ended_at: Optional[datetime] = None,
    ) -> Optional[InteractionMetrics]:
        """
        End tracking for an interaction and compute final metrics.
        
        Args:
            interaction_id: Target interaction.
            resolution_type: How the interaction was resolved.
            ended_at: End time (defaults to now).
            
        Returns:
            Final InteractionMetrics with computed values.
        """
        async with self._lock:
            metrics = self._interactions.get(interaction_id)
            if not metrics:
                return None
            
            # Set end time and duration
            metrics.ended_at = ended_at or datetime.now(timezone.utc)
            metrics.duration_seconds = (
                metrics.ended_at - metrics.started_at
            ).total_seconds()
            
            # Set resolution
            metrics.resolution_type = resolution_type
            
            # Compute confidence aggregates
            if metrics.confidence_scores:
                metrics.average_confidence = sum(metrics.confidence_scores) / len(
                    metrics.confidence_scores
                )
                metrics.min_confidence = min(metrics.confidence_scores)
                metrics.max_confidence = max(metrics.confidence_scores)
            
            # Get emotion history
            emotion_history = self._emotion_histories.get(interaction_id, [])
            
            # Compute CSAT
            csat, factors = compute_csat(
                resolution_type=resolution_type,
                average_confidence=metrics.average_confidence,
                duration_seconds=metrics.duration_seconds,
                turn_count=metrics.turn_count,
                emotion_history=emotion_history,
            )
            metrics.computed_csat = csat
            metrics.csat_factors = factors
            
            return metrics

    async def get_interaction_metrics(
        self,
        interaction_id: UUID,
    ) -> Optional[InteractionMetrics]:
        """Get metrics for a specific interaction."""
        return self._interactions.get(interaction_id)

    async def get_aggregated_metrics(
        self,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> AggregatedMetrics:
        """
        Get aggregated metrics for a time period.
        
        Args:
            period_start: Start of period (defaults to 24h ago).
            period_end: End of period (defaults to now).
            
        Returns:
            AggregatedMetrics with computed values.
        """
        async with self._lock:
            now = datetime.now(timezone.utc)
            period_start = period_start or (now - timedelta(hours=24))
            period_end = period_end or now
            
            # Filter interactions in period
            interactions = [
                m for m in self._interactions.values()
                if period_start <= m.started_at <= period_end
            ]
            
            if not interactions:
                return AggregatedMetrics(
                    period_start=period_start,
                    period_end=period_end,
                )
            
            # Volume metrics
            total = len(interactions)
            by_channel: Dict[str, int] = defaultdict(int)
            by_intent: Dict[str, int] = defaultdict(int)
            
            for m in interactions:
                by_channel[m.channel.value] += 1
                if m.primary_intent:
                    by_intent[m.primary_intent.value] += 1
            
            # Resolution metrics
            ai_resolved = sum(
                1 for m in interactions
                if m.resolution_type == ResolutionType.AI_RESOLVED
            )
            human_escalated = sum(
                1 for m in interactions
                if m.resolution_type == ResolutionType.HUMAN_ESCALATED
            )
            abandoned = sum(
                1 for m in interactions
                if m.resolution_type == ResolutionType.ABANDONED
            )
            
            completed = [m for m in interactions if m.resolution_type is not None]
            resolution_rate = ai_resolved / len(completed) if completed else 0.0
            escalation_rate = human_escalated / len(completed) if completed else 0.0
            
            # Duration metrics
            durations = [
                m.duration_seconds for m in interactions
                if m.duration_seconds is not None
            ]
            avg_duration = sum(durations) / len(durations) if durations else 0.0
            min_duration = min(durations) if durations else 0.0
            max_duration = max(durations) if durations else 0.0
            
            # Confidence metrics
            all_confidences = [
                c for m in interactions for c in m.confidence_scores
            ]
            avg_confidence = (
                sum(all_confidences) / len(all_confidences)
                if all_confidences else 0.0
            )
            
            confidence_dist: Dict[str, int] = defaultdict(int)
            for c in all_confidences:
                if c >= 0.8:
                    confidence_dist["high"] += 1
                elif c >= 0.5:
                    confidence_dist["medium"] += 1
                else:
                    confidence_dist["low"] += 1
            
            # CSAT metrics
            csat_scores = [
                m.computed_csat for m in interactions
                if m.computed_csat is not None
            ]
            avg_csat = sum(csat_scores) / len(csat_scores) if csat_scores else 0.0
            
            csat_dist: Dict[str, int] = defaultdict(int)
            for score in csat_scores:
                if score >= 4.5:
                    csat_dist["excellent"] += 1
                elif score >= 3.5:
                    csat_dist["good"] += 1
                elif score >= 2.5:
                    csat_dist["average"] += 1
                else:
                    csat_dist["poor"] += 1
            
            # Turn count average
            turn_counts = [m.turn_count for m in interactions]
            avg_turns = sum(turn_counts) / len(turn_counts) if turn_counts else 0.0
            
            return AggregatedMetrics(
                period_start=period_start,
                period_end=period_end,
                total_interactions=total,
                interactions_by_channel=dict(by_channel),
                interactions_by_intent=dict(by_intent),
                ai_resolved_count=ai_resolved,
                human_escalated_count=human_escalated,
                abandoned_count=abandoned,
                resolution_rate=round(resolution_rate, 3),
                escalation_rate=round(escalation_rate, 3),
                average_duration_seconds=round(avg_duration, 2),
                min_duration_seconds=round(min_duration, 2),
                max_duration_seconds=round(max_duration, 2),
                average_confidence=round(avg_confidence, 3),
                confidence_distribution=dict(confidence_dist),
                average_csat=round(avg_csat, 2),
                csat_distribution=dict(csat_dist),
                turn_count_average=round(avg_turns, 2),
            )

    async def get_agent_performance(
        self,
        agent_type: AgentType,
    ) -> AgentPerformanceMetrics:
        """
        Get performance metrics for an agent type.
        
        Args:
            agent_type: Type of agent to analyze.
            
        Returns:
            AgentPerformanceMetrics with computed values.
        """
        async with self._lock:
            decisions = self._agent_decisions.get(agent_type, [])
            
            if not decisions:
                return AgentPerformanceMetrics(
                    agent_type=agent_type,
                    decisions_made=0,
                )
            
            # Calculate confidence metrics
            confidences = [
                d["confidence"] for d in decisions
                if d.get("confidence") is not None
            ]
            
            avg_confidence = (
                sum(confidences) / len(confidences)
                if confidences else 0.0
            )
            high_rate = (
                sum(1 for c in confidences if c >= 0.8) / len(confidences)
                if confidences else 0.0
            )
            low_rate = (
                sum(1 for c in confidences if c < 0.5) / len(confidences)
                if confidences else 0.0
            )
            
            return AgentPerformanceMetrics(
                agent_type=agent_type,
                decisions_made=len(decisions),
                average_confidence=round(avg_confidence, 3),
                high_confidence_rate=round(high_rate, 3),
                low_confidence_rate=round(low_rate, 3),
            )

    async def get_confidence_trend(
        self,
        interaction_id: UUID,
    ) -> List[float]:
        """Get confidence scores over time for an interaction."""
        metrics = self._interactions.get(interaction_id)
        return metrics.confidence_scores if metrics else []

    async def get_emotion_trend(
        self,
        interaction_id: UUID,
    ) -> List[str]:
        """Get emotion progression for an interaction."""
        emotions = self._emotion_histories.get(interaction_id, [])
        return [e.value for e in emotions]

    async def get_summary(self) -> Dict:
        """Get a quick summary of current metrics."""
        async with self._lock:
            total = len(self._interactions)
            completed = sum(
                1 for m in self._interactions.values()
                if m.resolution_type is not None
            )
            active = total - completed
            
            return {
                "total_interactions": total,
                "active_interactions": active,
                "completed_interactions": completed,
                "agents_tracked": list(self._agent_decisions.keys()),
            }

    async def clear(self) -> int:
        """
        Clear all metrics. Use with caution - primarily for testing.
        
        Returns count of cleared interactions.
        """
        async with self._lock:
            count = len(self._interactions)
            self._interactions.clear()
            self._agent_decisions.clear()
            self._emotion_histories.clear()
            return count

"""
Analytics API Endpoints

Comprehensive analytics for call center operations.
Provides aggregated metrics, trends, and breakdowns.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from collections import defaultdict

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.persistence.store import get_store

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# -----------------------------------------------------------------------------
# Response Models
# -----------------------------------------------------------------------------

class CallsPerHourItem(BaseModel):
    """Hourly call distribution."""
    hour: int = Field(ge=0, le=23)
    count: int = Field(ge=0)


class DailyTrendItem(BaseModel):
    """Daily trend data point."""
    date: str
    total: int
    resolved: int
    escalated: int
    averageConfidence: float


class ChannelBreakdown(BaseModel):
    """Breakdown by channel."""
    channel: str
    count: int
    percentage: float


class StatusBreakdown(BaseModel):
    """Breakdown by status."""
    status: str
    count: int
    percentage: float


class AgentPerformance(BaseModel):
    """Agent performance metrics."""
    agentType: str
    totalDecisions: int
    averageConfidence: float
    averageProcessingMs: float


class AnalyticsSummary(BaseModel):
    """Core analytics summary."""
    totalInteractions: int = Field(description="Total interactions")
    activeInteractions: int = Field(description="Currently active")
    completedInteractions: int = Field(description="Completed interactions")
    escalatedInteractions: int = Field(description="Escalated to human")
    resolutionRate: float = Field(description="AI resolution rate (0-1)")
    escalationRate: float = Field(description="Escalation rate (0-1)")
    averageConfidence: float = Field(description="Average AI confidence (0-1)")
    averageDurationSeconds: float = Field(description="Average call duration")
    averageMessagesPerCall: float = Field(description="Average messages per call")


class AnalyticsOverview(BaseModel):
    """Complete analytics overview."""
    summary: AnalyticsSummary
    callsPerHour: List[CallsPerHourItem]
    channelBreakdown: List[ChannelBreakdown]
    statusBreakdown: List[StatusBreakdown]
    agentPerformance: List[AgentPerformance]
    periodStart: str
    periodEnd: str


class TrendsResponse(BaseModel):
    """Time-based trends response."""
    daily: List[DailyTrendItem]
    periodStart: str
    periodEnd: str
    totalDays: int


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def _parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO datetime string."""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None


def _calculate_percentage(count: int, total: int) -> float:
    """Calculate percentage safely."""
    return round(count / total * 100, 1) if total > 0 else 0.0


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get(
    "/metrics",
    response_model=AnalyticsSummary,
    summary="Get summary metrics",
    description="Returns core analytics metrics for the dashboard.",
)
async def get_metrics() -> AnalyticsSummary:
    """
    Get core analytics summary.
    
    Returns key metrics including resolution rates,
    confidence scores, and call statistics.
    """
    store = get_store()
    interactions = store.list_interactions(limit=10000)
    
    total = len(interactions)
    completed = sum(1 for i in interactions if i.status == "completed")
    escalated = sum(1 for i in interactions if i.status == "escalated")
    active = sum(1 for i in interactions if i.status in ("initiated", "in_progress"))
    
    # Calculate durations
    durations: List[float] = []
    message_counts: List[int] = []
    
    for interaction in interactions:
        started = _parse_datetime(interaction.started_at)
        ended = _parse_datetime(interaction.ended_at)
        if started and ended:
            durations.append((ended - started).total_seconds())
        message_counts.append(interaction.message_count)
    
    avg_duration = sum(durations) / len(durations) if durations else 0
    avg_messages = sum(message_counts) / len(message_counts) if message_counts else 0
    
    # Calculate confidence from decisions
    total_confidence = 0.0
    decision_count = 0
    
    for interaction in interactions[:100]:  # Sample for efficiency
        decisions = store.get_agent_decisions(interaction.interaction_id)
        for d in decisions:
            total_confidence += d.confidence
            decision_count += 1
    
    avg_confidence = total_confidence / decision_count if decision_count > 0 else 0.75
    
    # Calculate rates
    resolved_or_escalated = completed + escalated
    resolution_rate = completed / resolved_or_escalated if resolved_or_escalated > 0 else 0
    escalation_rate = escalated / resolved_or_escalated if resolved_or_escalated > 0 else 0
    
    return AnalyticsSummary(
        totalInteractions=total,
        activeInteractions=active,
        completedInteractions=completed,
        escalatedInteractions=escalated,
        resolutionRate=round(resolution_rate, 3),
        escalationRate=round(escalation_rate, 3),
        averageConfidence=round(avg_confidence, 3),
        averageDurationSeconds=round(avg_duration, 1),
        averageMessagesPerCall=round(avg_messages, 1),
    )


@router.get(
    "/overview",
    response_model=AnalyticsOverview,
    summary="Get analytics overview",
    description="Returns comprehensive analytics with breakdowns.",
)
async def get_overview(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
) -> AnalyticsOverview:
    """
    Get complete analytics overview.
    
    Includes summary metrics, channel breakdown,
    status breakdown, and agent performance.
    """
    store = get_store()
    now = datetime.now(timezone.utc)
    period_start = now - timedelta(days=days)
    
    interactions = store.list_interactions(limit=10000)
    
    # Filter by period
    filtered = []
    for interaction in interactions:
        started = _parse_datetime(interaction.started_at)
        if started and started >= period_start:
            filtered.append(interaction)
    
    total = len(filtered)
    completed = sum(1 for i in filtered if i.status == "completed")
    escalated = sum(1 for i in filtered if i.status == "escalated")
    active = sum(1 for i in filtered if i.status in ("initiated", "in_progress"))
    
    # Calculate durations and messages
    durations: List[float] = []
    message_counts: List[int] = []
    
    for interaction in filtered:
        started = _parse_datetime(interaction.started_at)
        ended = _parse_datetime(interaction.ended_at)
        if started and ended:
            durations.append((ended - started).total_seconds())
        message_counts.append(interaction.message_count)
    
    avg_duration = sum(durations) / len(durations) if durations else 0
    avg_messages = sum(message_counts) / len(message_counts) if message_counts else 0
    
    # Channel breakdown
    channel_counts: Dict[str, int] = defaultdict(int)
    for i in filtered:
        channel_counts[i.channel] += 1
    
    channel_breakdown = [
        ChannelBreakdown(
            channel=channel,
            count=count,
            percentage=_calculate_percentage(count, total),
        )
        for channel, count in sorted(channel_counts.items())
    ]
    
    # Status breakdown
    status_counts: Dict[str, int] = defaultdict(int)
    for i in filtered:
        status_counts[i.status] += 1
    
    status_breakdown = [
        StatusBreakdown(
            status=status,
            count=count,
            percentage=_calculate_percentage(count, total),
        )
        for status, count in sorted(status_counts.items())
    ]
    
    # Calls per hour
    hourly_counts: Dict[int, int] = defaultdict(int)
    for interaction in filtered:
        started = _parse_datetime(interaction.started_at)
        if started:
            hourly_counts[started.hour] += 1
    
    calls_per_hour = [
        CallsPerHourItem(hour=h, count=hourly_counts.get(h, 0))
        for h in range(24)
    ]
    
    # Agent performance
    agent_stats: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "confidence": 0.0, "processing_ms": 0}
    )
    
    for interaction in filtered[:100]:  # Sample for efficiency
        decisions = store.get_agent_decisions(interaction.interaction_id)
        for d in decisions:
            stats = agent_stats[d.agent_type]
            stats["count"] += 1
            stats["confidence"] += d.confidence
            stats["processing_ms"] += d.processing_time_ms
    
    agent_performance = [
        AgentPerformance(
            agentType=agent_type,
            totalDecisions=stats["count"],
            averageConfidence=round(stats["confidence"] / stats["count"], 3) if stats["count"] > 0 else 0,
            averageProcessingMs=round(stats["processing_ms"] / stats["count"], 1) if stats["count"] > 0 else 0,
        )
        for agent_type, stats in sorted(agent_stats.items())
    ]
    
    # Calculate rates
    resolved_or_escalated = completed + escalated
    resolution_rate = completed / resolved_or_escalated if resolved_or_escalated > 0 else 0
    escalation_rate = escalated / resolved_or_escalated if resolved_or_escalated > 0 else 0
    
    # Get average confidence
    total_confidence = sum(s["confidence"] for s in agent_stats.values())
    total_decisions = sum(s["count"] for s in agent_stats.values())
    avg_confidence = total_confidence / total_decisions if total_decisions > 0 else 0.75
    
    summary = AnalyticsSummary(
        totalInteractions=total,
        activeInteractions=active,
        completedInteractions=completed,
        escalatedInteractions=escalated,
        resolutionRate=round(resolution_rate, 3),
        escalationRate=round(escalation_rate, 3),
        averageConfidence=round(avg_confidence, 3),
        averageDurationSeconds=round(avg_duration, 1),
        averageMessagesPerCall=round(avg_messages, 1),
    )
    
    return AnalyticsOverview(
        summary=summary,
        callsPerHour=calls_per_hour,
        channelBreakdown=channel_breakdown,
        statusBreakdown=status_breakdown,
        agentPerformance=agent_performance,
        periodStart=period_start.isoformat(),
        periodEnd=now.isoformat(),
    )


@router.get(
    "/trends",
    response_model=TrendsResponse,
    summary="Get time-based trends",
    description="Returns daily trends for calls, resolutions, and confidence.",
)
async def get_trends(
    days: int = Query(7, ge=1, le=30, description="Number of days"),
) -> TrendsResponse:
    """
    Get daily trends.
    
    Shows how metrics change over time for
    identifying patterns and anomalies.
    """
    store = get_store()
    now = datetime.now(timezone.utc)
    period_start = now - timedelta(days=days)
    
    interactions = store.list_interactions(limit=10000)
    
    # Group by date
    daily_data: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"total": 0, "resolved": 0, "escalated": 0, "confidence": 0.0, "decision_count": 0}
    )
    
    for interaction in interactions:
        started = _parse_datetime(interaction.started_at)
        if not started or started < period_start:
            continue
        
        date_key = started.strftime("%Y-%m-%d")
        daily_data[date_key]["total"] += 1
        
        if interaction.status == "completed":
            daily_data[date_key]["resolved"] += 1
        elif interaction.status == "escalated":
            daily_data[date_key]["escalated"] += 1
        
        # Get decisions for confidence
        decisions = store.get_agent_decisions(interaction.interaction_id)
        for d in decisions:
            daily_data[date_key]["confidence"] += d.confidence
            daily_data[date_key]["decision_count"] += 1
    
    # Build trend items
    daily_trends: List[DailyTrendItem] = []
    
    for i in range(days):
        date = (period_start + timedelta(days=i)).strftime("%Y-%m-%d")
        data = daily_data.get(date, {"total": 0, "resolved": 0, "escalated": 0, "confidence": 0, "decision_count": 0})
        
        avg_conf = data["confidence"] / data["decision_count"] if data["decision_count"] > 0 else 0
        
        daily_trends.append(DailyTrendItem(
            date=date,
            total=data["total"],
            resolved=data["resolved"],
            escalated=data["escalated"],
            averageConfidence=round(avg_conf, 3),
        ))
    
    return TrendsResponse(
        daily=daily_trends,
        periodStart=period_start.isoformat(),
        periodEnd=now.isoformat(),
        totalDays=days,
    )


@router.get(
    "/agents",
    response_model=List[AgentPerformance],
    summary="Get agent analytics",
    description="Returns performance metrics for each agent type.",
)
async def get_agent_analytics() -> List[AgentPerformance]:
    """
    Get agent performance analytics.
    
    Shows decision counts, confidence levels,
    and processing times per agent type.
    """
    store = get_store()
    interactions = store.list_interactions(limit=500)
    
    agent_stats: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "confidence": 0.0, "processing_ms": 0}
    )
    
    for interaction in interactions:
        decisions = store.get_agent_decisions(interaction.interaction_id)
        for d in decisions:
            stats = agent_stats[d.agent_type]
            stats["count"] += 1
            stats["confidence"] += d.confidence
            stats["processing_ms"] += d.processing_time_ms
    
    return [
        AgentPerformance(
            agentType=agent_type,
            totalDecisions=stats["count"],
            averageConfidence=round(stats["confidence"] / stats["count"], 3) if stats["count"] > 0 else 0,
            averageProcessingMs=round(stats["processing_ms"] / stats["count"], 1) if stats["count"] > 0 else 0,
        )
        for agent_type, stats in sorted(agent_stats.items())
    ]


@router.get(
    "/channels",
    response_model=List[ChannelBreakdown],
    summary="Get channel analytics",
    description="Returns breakdown of calls by channel.",
)
async def get_channel_analytics() -> List[ChannelBreakdown]:
    """
    Get channel breakdown.
    
    Shows distribution of calls across
    voice and chat channels.
    """
    store = get_store()
    interactions = store.list_interactions(limit=10000)
    
    total = len(interactions)
    channel_counts: Dict[str, int] = defaultdict(int)
    
    for i in interactions:
        channel_counts[i.channel] += 1
    
    return [
        ChannelBreakdown(
            channel=channel,
            count=count,
            percentage=_calculate_percentage(count, total),
        )
        for channel, count in sorted(channel_counts.items())
    ]


@router.get(
    "/resolution",
    summary="Get resolution analytics",
    description="Returns resolution and escalation statistics.",
)
async def get_resolution_analytics() -> dict:
    """
    Get resolution statistics.
    
    Shows how calls are being resolved and
    reasons for escalation.
    """
    store = get_store()
    interactions = store.list_interactions(limit=10000)
    
    total = len(interactions)
    completed = sum(1 for i in interactions if i.status == "completed")
    escalated = sum(1 for i in interactions if i.status == "escalated")
    active = sum(1 for i in interactions if i.status in ("initiated", "in_progress"))
    abandoned = sum(1 for i in interactions if i.status == "abandoned")
    
    # Resolution breakdown
    resolved_or_escalated = completed + escalated
    
    return {
        "total": total,
        "breakdown": {
            "completed": {
                "count": completed,
                "percentage": _calculate_percentage(completed, total),
            },
            "escalated": {
                "count": escalated,
                "percentage": _calculate_percentage(escalated, total),
            },
            "active": {
                "count": active,
                "percentage": _calculate_percentage(active, total),
            },
            "abandoned": {
                "count": abandoned,
                "percentage": _calculate_percentage(abandoned, total),
            },
        },
        "rates": {
            "resolutionRate": round(completed / resolved_or_escalated, 3) if resolved_or_escalated > 0 else 0,
            "escalationRate": round(escalated / resolved_or_escalated, 3) if resolved_or_escalated > 0 else 0,
            "abandonmentRate": round(abandoned / total, 3) if total > 0 else 0,
        },
    }


@router.get(
    "/health",
    summary="Analytics service health",
    description="Check if the analytics service is operational.",
)
async def analytics_health():
    """Health check for analytics service."""
    return {
        "status": "operational",
        "service": "analytics",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

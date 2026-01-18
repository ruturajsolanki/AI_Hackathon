"""
Agent Metadata API Routes

Read-only endpoints exposing agent information, responsibilities,
and anonymized decision examples. No internal prompts or configuration exposed.
"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.persistence.store import get_store

router = APIRouter(prefix="/agents", tags=["Agents"])


# -----------------------------------------------------------------------------
# Response Models
# -----------------------------------------------------------------------------

class AgentCapability(BaseModel):
    """A single capability of an agent."""
    name: str
    description: str


class DecisionScope(BaseModel):
    """Defines what decisions an agent can make."""
    autonomous_actions: List[str] = Field(
        description="Actions the agent can take without approval"
    )
    requires_review: List[str] = Field(
        description="Actions that require supervisor review"
    )
    cannot_perform: List[str] = Field(
        description="Actions outside the agent's authority"
    )


class AnonymizedDecision(BaseModel):
    """An anonymized example of a decision made by this agent."""
    decision_type: str
    summary: str
    confidence: float
    confidence_level: str
    processing_time_ms: int
    timestamp: datetime


class AgentMetadata(BaseModel):
    """Complete metadata for an agent."""
    agent_id: str
    name: str
    type: str
    description: str
    status: str
    responsibilities: List[str]
    capabilities: List[AgentCapability]
    decision_scope: DecisionScope
    metrics: dict = Field(default_factory=dict)


class AgentListResponse(BaseModel):
    """Response for listing all agents."""
    agents: List[AgentMetadata]
    total: int


class AgentDetailResponse(BaseModel):
    """Detailed agent information with recent decisions."""
    agent: AgentMetadata
    recent_decisions: List[AnonymizedDecision]
    total_decisions: int


# -----------------------------------------------------------------------------
# Agent Definitions (Static metadata - no prompts exposed)
# -----------------------------------------------------------------------------

AGENT_DEFINITIONS = {
    "primary": AgentMetadata(
        agent_id="primary",
        name="Primary Interaction Agent",
        type="primary",
        description="First-line agent that handles initial customer interactions, "
                    "understands intent, detects emotion, and drafts responses.",
        status="active",
        responsibilities=[
            "Greet customers and establish rapport",
            "Analyze customer messages to detect intent",
            "Assess customer emotional state",
            "Draft appropriate responses",
            "Provide initial confidence assessment",
            "Route complex issues for review",
        ],
        capabilities=[
            AgentCapability(
                name="Intent Detection",
                description="Identifies customer intent from natural language"
            ),
            AgentCapability(
                name="Emotion Analysis",
                description="Detects customer emotional state (calm, frustrated, urgent)"
            ),
            AgentCapability(
                name="Response Generation",
                description="Creates helpful, professional responses"
            ),
            AgentCapability(
                name="Context Awareness",
                description="Maintains conversation context across turns"
            ),
        ],
        decision_scope=DecisionScope(
            autonomous_actions=[
                "Answer general inquiries",
                "Provide account information",
                "Process simple requests",
                "Acknowledge complaints",
            ],
            requires_review=[
                "Issue refunds or credits",
                "Modify account settings",
                "Handle sensitive data requests",
                "Escalate to human agent",
            ],
            cannot_perform=[
                "Access payment systems directly",
                "Override security policies",
                "Make promises outside policy",
                "Share customer data externally",
            ],
        ),
    ),
    "supervisor": AgentMetadata(
        agent_id="supervisor",
        name="Supervisor Agent",
        type="supervisor",
        description="Reviews primary agent decisions for quality, compliance, "
                    "and appropriate tone before responses are sent.",
        status="active",
        responsibilities=[
            "Review response quality and accuracy",
            "Ensure compliance with policies",
            "Validate tone appropriateness",
            "Adjust confidence scores",
            "Flag potential risks",
            "Approve or request revision",
        ],
        capabilities=[
            AgentCapability(
                name="Quality Assessment",
                description="Evaluates response accuracy and helpfulness"
            ),
            AgentCapability(
                name="Compliance Check",
                description="Verifies adherence to company policies"
            ),
            AgentCapability(
                name="Tone Analysis",
                description="Ensures professional and empathetic communication"
            ),
            AgentCapability(
                name="Risk Detection",
                description="Identifies potential issues or escalation triggers"
            ),
        ],
        decision_scope=DecisionScope(
            autonomous_actions=[
                "Approve standard responses",
                "Adjust confidence levels",
                "Add compliance notes",
                "Flag for monitoring",
            ],
            requires_review=[
                "Override primary agent decisions",
                "Trigger immediate escalation",
                "Block response delivery",
            ],
            cannot_perform=[
                "Interact directly with customers",
                "Access customer payment data",
                "Modify agent configurations",
                "Bypass escalation protocols",
            ],
        ),
    ),
    "escalation": AgentMetadata(
        agent_id="escalation",
        name="Escalation Handler Agent",
        type="escalation",
        description="Determines when and how to escalate interactions to human agents "
                    "or create support tickets based on supervisor reviews.",
        status="active",
        responsibilities=[
            "Evaluate escalation necessity",
            "Determine escalation type",
            "Route to appropriate human team",
            "Create support tickets",
            "Preserve context for handoff",
            "Track escalation outcomes",
        ],
        capabilities=[
            AgentCapability(
                name="Escalation Assessment",
                description="Determines if human intervention is needed"
            ),
            AgentCapability(
                name="Routing Logic",
                description="Selects appropriate escalation path"
            ),
            AgentCapability(
                name="Context Summarization",
                description="Prepares handoff summary for human agents"
            ),
            AgentCapability(
                name="Priority Assignment",
                description="Sets urgency level for escalated cases"
            ),
        ],
        decision_scope=DecisionScope(
            autonomous_actions=[
                "Recommend escalation path",
                "Create support tickets",
                "Set priority levels",
                "Generate context summaries",
            ],
            requires_review=[
                "Emergency escalations",
                "VIP customer handling",
                "Legal or compliance issues",
            ],
            cannot_perform=[
                "Resolve issues independently",
                "Override customer requests",
                "Contact customers directly",
                "Access external systems",
            ],
        ),
    ),
}


# -----------------------------------------------------------------------------
# API Routes
# -----------------------------------------------------------------------------

@router.get(
    "",
    response_model=AgentListResponse,
    summary="List all agents",
    description="Returns metadata for all available AI agents in the system.",
)
async def list_agents() -> AgentListResponse:
    """
    List all available agents with their metadata.
    
    Returns basic information about each agent including
    responsibilities and capabilities.
    """
    store = get_store()
    
    # Get decision counts per agent type
    agents_with_metrics = []
    for agent_id, agent in AGENT_DEFINITIONS.items():
        # Get metrics from recent decisions
        all_interactions = store.list_interactions(limit=100)
        total_decisions = 0
        total_confidence = 0.0
        
        for interaction in all_interactions:
            decisions = store.get_agent_decisions(
                UUID(interaction.interaction_id),
                agent_type=agent_id
            )
            total_decisions += len(decisions)
            total_confidence += sum(d.confidence for d in decisions)
        
        avg_confidence = total_confidence / total_decisions if total_decisions > 0 else 0
        
        agent_with_metrics = agent.model_copy()
        agent_with_metrics.metrics = {
            "total_decisions": total_decisions,
            "average_confidence": round(avg_confidence, 3),
        }
        agents_with_metrics.append(agent_with_metrics)
    
    return AgentListResponse(
        agents=agents_with_metrics,
        total=len(agents_with_metrics),
    )


@router.get(
    "/{agent_id}",
    response_model=AgentDetailResponse,
    summary="Get agent details",
    description="Returns detailed information about a specific agent "
                "including recent anonymized decision examples.",
    responses={
        404: {"description": "Agent not found"},
    },
)
async def get_agent(
    agent_id: str,
    limit: int = Query(10, ge=1, le=50, description="Number of recent decisions to return"),
) -> AgentDetailResponse:
    """
    Get detailed information about a specific agent.
    
    Includes recent anonymized decision examples to illustrate
    how the agent operates.
    """
    if agent_id not in AGENT_DEFINITIONS:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )
    
    agent = AGENT_DEFINITIONS[agent_id]
    store = get_store()
    
    # Collect recent decisions for this agent type (anonymized)
    recent_decisions: List[AnonymizedDecision] = []
    total_decisions = 0
    total_confidence = 0.0
    
    all_interactions = store.list_interactions(limit=200)
    
    for interaction in all_interactions:
        decisions = store.get_agent_decisions(
            UUID(interaction.interaction_id),
            agent_type=agent_id
        )
        total_decisions += len(decisions)
        
        for decision in decisions:
            total_confidence += decision.confidence
            
            if len(recent_decisions) < limit:
                # Parse timestamp
                try:
                    timestamp = datetime.fromisoformat(
                        decision.timestamp.replace('Z', '+00:00')
                    )
                except (ValueError, AttributeError):
                    timestamp = datetime.now(timezone.utc)
                
                # Anonymize the decision summary
                anonymized_summary = _anonymize_summary(decision.decision_type)
                
                recent_decisions.append(AnonymizedDecision(
                    decision_type=decision.decision_type,
                    summary=anonymized_summary,
                    confidence=decision.confidence,
                    confidence_level=decision.confidence_level,
                    processing_time_ms=decision.processing_time_ms,
                    timestamp=timestamp,
                ))
    
    # Sort by timestamp descending
    recent_decisions.sort(key=lambda d: d.timestamp, reverse=True)
    recent_decisions = recent_decisions[:limit]
    
    # Calculate metrics
    avg_confidence = total_confidence / total_decisions if total_decisions > 0 else 0
    agent_with_metrics = agent.model_copy()
    agent_with_metrics.metrics = {
        "total_decisions": total_decisions,
        "average_confidence": round(avg_confidence, 3),
        "decisions_last_24h": sum(
            1 for d in recent_decisions 
            if (datetime.now(timezone.utc) - d.timestamp).days < 1
        ),
    }
    
    return AgentDetailResponse(
        agent=agent_with_metrics,
        recent_decisions=recent_decisions,
        total_decisions=total_decisions,
    )


@router.get(
    "/{agent_id}/decisions",
    response_model=List[AnonymizedDecision],
    summary="Get agent decisions",
    description="Returns recent anonymized decisions made by this agent.",
    responses={
        404: {"description": "Agent not found"},
    },
)
async def get_agent_decisions(
    agent_id: str,
    limit: int = Query(20, ge=1, le=100, description="Number of decisions to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> List[AnonymizedDecision]:
    """
    Get recent decisions made by a specific agent.
    
    All decisions are anonymized - no customer data is exposed.
    """
    if agent_id not in AGENT_DEFINITIONS:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )
    
    store = get_store()
    decisions: List[AnonymizedDecision] = []
    
    all_interactions = store.list_interactions(limit=500)
    
    for interaction in all_interactions:
        agent_decisions = store.get_agent_decisions(
            UUID(interaction.interaction_id),
            agent_type=agent_id
        )
        
        for decision in agent_decisions:
            try:
                timestamp = datetime.fromisoformat(
                    decision.timestamp.replace('Z', '+00:00')
                )
            except (ValueError, AttributeError):
                timestamp = datetime.now(timezone.utc)
            
            decisions.append(AnonymizedDecision(
                decision_type=decision.decision_type,
                summary=_anonymize_summary(decision.decision_type),
                confidence=decision.confidence,
                confidence_level=decision.confidence_level,
                processing_time_ms=decision.processing_time_ms,
                timestamp=timestamp,
            ))
    
    # Sort by timestamp descending and paginate
    decisions.sort(key=lambda d: d.timestamp, reverse=True)
    return decisions[offset:offset + limit]


@router.get(
    "/{agent_id}/capabilities",
    response_model=List[AgentCapability],
    summary="Get agent capabilities",
    description="Returns the capabilities of a specific agent.",
    responses={
        404: {"description": "Agent not found"},
    },
)
async def get_agent_capabilities(agent_id: str) -> List[AgentCapability]:
    """
    Get the capabilities of a specific agent.
    """
    if agent_id not in AGENT_DEFINITIONS:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )
    
    return AGENT_DEFINITIONS[agent_id].capabilities


@router.get(
    "/{agent_id}/scope",
    response_model=DecisionScope,
    summary="Get agent decision scope",
    description="Returns what decisions an agent can and cannot make.",
    responses={
        404: {"description": "Agent not found"},
    },
)
async def get_agent_scope(agent_id: str) -> DecisionScope:
    """
    Get the decision scope of a specific agent.
    
    Defines autonomous actions, actions requiring review,
    and actions outside the agent's authority.
    """
    if agent_id not in AGENT_DEFINITIONS:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )
    
    return AGENT_DEFINITIONS[agent_id].decision_scope


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def _anonymize_summary(decision_type: str) -> str:
    """
    Generate an anonymized summary based on decision type.
    No customer data is exposed.
    """
    summaries = {
        "intent_detected": "Identified customer intent from message",
        "response_generated": "Generated appropriate response",
        "emotion_assessed": "Assessed customer emotional state",
        "approved": "Approved response for delivery",
        "flagged": "Flagged for additional review",
        "escalation_recommended": "Recommended escalation to human agent",
        "ticket_created": "Created support ticket",
        "retry_primary": "Requested primary agent retry",
        "none": "No action required",
    }
    
    # Normalize decision type
    normalized = decision_type.lower().replace(" ", "_").replace("-", "_")
    
    # Check for partial matches
    for key, summary in summaries.items():
        if key in normalized or normalized in key:
            return summary
    
    # Default summary
    return f"Processed {decision_type.replace('_', ' ')} decision"

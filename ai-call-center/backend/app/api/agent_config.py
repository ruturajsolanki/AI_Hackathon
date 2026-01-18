"""
Agent Configuration API

Provides CRUD operations for agent prompts and LLM settings.
Allows runtime configuration of Primary, Supervisor, and Escalation agents.

Security Note:
- Prompt changes are stored in-memory (production should use database)
- All changes are audited
- Original prompts preserved as fallback
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Agent Configuration Store (In-Memory)
# -----------------------------------------------------------------------------

class AgentPromptConfig(BaseModel):
    """Configuration for a single agent's prompts and settings."""
    
    agent_id: str
    agent_name: str
    agent_type: str  # primary, supervisor, escalation
    description: str
    
    # Prompts
    system_prompt: str
    user_prompt_template: str
    
    # LLM Settings
    model: str = "gpt-4o-mini"
    temperature: float = 0.3
    max_tokens: int = 1024
    top_p: float = 1.0
    
    # Behavior Settings
    confidence_threshold: float = 0.7
    fallback_enabled: bool = True
    
    # Output Schema (JSON)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    version: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: Optional[str] = None
    
    # Is this the default or custom?
    is_custom: bool = False


class AgentConfigStore:
    """
    In-memory store for agent configurations.
    
    Production: Replace with MongoDB storage.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._configs: Dict[str, AgentPromptConfig] = {}
            cls._instance._history: List[Dict] = []
            cls._instance._initialize_defaults()
        return cls._instance
    
    def _initialize_defaults(self):
        """Load default configurations from prompts.py."""
        from app.agents.prompts import (
            PRIMARY_AGENT_SYSTEM_PROMPT,
            PRIMARY_AGENT_USER_PROMPT_TEMPLATE,
            PRIMARY_AGENT_OUTPUT_SCHEMA,
            SUPERVISOR_AGENT_SYSTEM_PROMPT,
            SUPERVISOR_AGENT_USER_PROMPT_TEMPLATE,
            SUPERVISOR_AGENT_OUTPUT_SCHEMA,
        )
        
        # Primary Agent
        self._configs["primary"] = AgentPromptConfig(
            agent_id="primary",
            agent_name="Primary Interaction Agent",
            agent_type="primary",
            description="First point of contact. Handles intent detection, emotion assessment, and initial response generation.",
            system_prompt=PRIMARY_AGENT_SYSTEM_PROMPT,
            user_prompt_template=PRIMARY_AGENT_USER_PROMPT_TEMPLATE,
            output_schema=PRIMARY_AGENT_OUTPUT_SCHEMA,
            model="gpt-4o-mini",
            temperature=0.3,
            confidence_threshold=0.7,
        )
        
        # Supervisor Agent
        self._configs["supervisor"] = AgentPromptConfig(
            agent_id="supervisor",
            agent_name="Supervisor Review Agent",
            agent_type="supervisor",
            description="Reviews Primary Agent decisions for quality, tone, and compliance. Adjusts confidence scores.",
            system_prompt=SUPERVISOR_AGENT_SYSTEM_PROMPT,
            user_prompt_template=SUPERVISOR_AGENT_USER_PROMPT_TEMPLATE,
            output_schema=SUPERVISOR_AGENT_OUTPUT_SCHEMA,
            model="gpt-4o-mini",
            temperature=0.2,
            confidence_threshold=0.6,
        )
        
        # Escalation Agent (rule-based, minimal LLM)
        self._configs["escalation"] = AgentPromptConfig(
            agent_id="escalation",
            agent_name="Escalation Decision Agent",
            agent_type="escalation",
            description="Determines when to escalate to human agents. Uses rule-based logic with optional LLM support.",
            system_prompt="""You are an Escalation Decision Agent.

Your role is to determine whether a customer interaction should be:
1. Continued by AI
2. Escalated to a human agent
3. Converted to a support ticket

## Escalation Criteria

### Immediate Escalation Required:
- Customer explicitly requests human agent
- Safety or legal concerns detected
- Compliance violation flagged
- Customer shows severe distress

### Consider Escalation:
- Confidence below threshold after multiple turns
- Customer frustration not improving
- Complex issue requiring account access
- Repeated failed resolution attempts

### Do Not Escalate:
- Customer is satisfied
- Issue resolved successfully
- Simple informational queries

Output your decision as structured JSON.""",
            user_prompt_template="""## Situation Analysis

### Supervisor Review
- Approved: {approved}
- Quality Score: {quality_score}
- Risk Level: {risk_level}
- Compliance: {compliance_status}
- Adjusted Confidence: {adjusted_confidence}
- Flags: {flags}

### Customer State
- Emotion: {emotion}
- Turn Count: {turn_count}
- Previous Escalations: {escalation_count}

### Original Message
{customer_message}

## Task
Decide: Should this be escalated?
Return JSON with:
- should_escalate: boolean
- escalation_type: "none" | "human_immediate" | "human_queue" | "ticket"
- reason: string explanation
- priority: 1-5 (1=highest)""",
            output_schema={
                "type": "object",
                "required": ["should_escalate", "escalation_type", "reason", "priority"],
                "properties": {
                    "should_escalate": {"type": "boolean"},
                    "escalation_type": {
                        "type": "string",
                        "enum": ["none", "human_immediate", "human_queue", "ticket"]
                    },
                    "reason": {"type": "string"},
                    "priority": {"type": "integer", "minimum": 1, "maximum": 5}
                }
            },
            model="gpt-4o-mini",
            temperature=0.1,  # More deterministic
            confidence_threshold=0.5,
            fallback_enabled=True,  # Use rule-based fallback
        )
    
    def get_config(self, agent_id: str) -> Optional[AgentPromptConfig]:
        """Get configuration for an agent."""
        return self._configs.get(agent_id)
    
    def get_all_configs(self) -> List[AgentPromptConfig]:
        """Get all agent configurations."""
        return list(self._configs.values())
    
    def update_config(
        self, 
        agent_id: str, 
        updates: Dict[str, Any],
        updated_by: str = "system"
    ) -> AgentPromptConfig:
        """Update an agent's configuration."""
        if agent_id not in self._configs:
            raise ValueError(f"Agent {agent_id} not found")
        
        current = self._configs[agent_id]
        
        # Save to history
        self._history.append({
            "agent_id": agent_id,
            "action": "update",
            "previous": current.model_dump(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "updated_by": updated_by,
        })
        
        # Apply updates
        updated_data = current.model_dump()
        for key, value in updates.items():
            if key in updated_data and key not in ["agent_id", "created_at"]:
                updated_data[key] = value
        
        updated_data["updated_at"] = datetime.now(timezone.utc)
        updated_data["updated_by"] = updated_by
        updated_data["is_custom"] = True
        updated_data["version"] = current.version + 1
        
        self._configs[agent_id] = AgentPromptConfig(**updated_data)
        
        logger.info(f"Agent config updated: {agent_id} by {updated_by}")
        return self._configs[agent_id]
    
    def reset_to_default(self, agent_id: str) -> AgentPromptConfig:
        """Reset an agent's configuration to defaults."""
        if agent_id not in self._configs:
            raise ValueError(f"Agent {agent_id} not found")
        
        # Save to history
        self._history.append({
            "agent_id": agent_id,
            "action": "reset",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        
        # Re-initialize defaults
        self._initialize_defaults()
        
        logger.info(f"Agent config reset to default: {agent_id}")
        return self._configs[agent_id]
    
    def get_history(self, agent_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get configuration change history."""
        if agent_id:
            filtered = [h for h in self._history if h.get("agent_id") == agent_id]
        else:
            filtered = self._history
        return filtered[-limit:]


def get_agent_config_store() -> AgentConfigStore:
    """Get the agent config store singleton."""
    return AgentConfigStore()


# -----------------------------------------------------------------------------
# Request/Response Models
# -----------------------------------------------------------------------------

class AgentConfigSummary(BaseModel):
    """Summary view of agent configuration."""
    agent_id: str
    agent_name: str
    agent_type: str
    description: str
    model: str
    temperature: float
    confidence_threshold: float
    is_custom: bool
    version: int
    updated_at: datetime


class AgentConfigDetail(BaseModel):
    """Full agent configuration."""
    agent_id: str
    agent_name: str
    agent_type: str
    description: str
    system_prompt: str
    user_prompt_template: str
    output_schema: Dict[str, Any]
    model: str
    temperature: float
    max_tokens: int
    top_p: float
    confidence_threshold: float
    fallback_enabled: bool
    is_custom: bool
    version: int
    created_at: datetime
    updated_at: datetime
    updated_by: Optional[str]


class UpdateAgentConfigRequest(BaseModel):
    """Request to update agent configuration."""
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=4096)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    fallback_enabled: Optional[bool] = None
    output_schema: Optional[Dict[str, Any]] = None


class TestPromptRequest(BaseModel):
    """Request to test a prompt configuration."""
    system_prompt: str
    user_prompt: str
    model: str = "gpt-4o-mini"
    temperature: float = 0.3
    test_input: str = "Hello, I have a question about my bill."


class TestPromptResponse(BaseModel):
    """Response from prompt test."""
    success: bool
    output: Optional[str] = None
    parsed_output: Optional[Dict[str, Any]] = None
    latency_ms: int
    tokens_used: Optional[int] = None
    error: Optional[str] = None


# -----------------------------------------------------------------------------
# Router
# -----------------------------------------------------------------------------

router = APIRouter(prefix="/agent-config", tags=["Agent Configuration"])


@router.get(
    "",
    response_model=List[AgentConfigSummary],
    summary="List all agent configurations",
)
async def list_agent_configs() -> List[AgentConfigSummary]:
    """Get summary of all agent configurations."""
    store = get_agent_config_store()
    configs = store.get_all_configs()
    
    return [
        AgentConfigSummary(
            agent_id=c.agent_id,
            agent_name=c.agent_name,
            agent_type=c.agent_type,
            description=c.description,
            model=c.model,
            temperature=c.temperature,
            confidence_threshold=c.confidence_threshold,
            is_custom=c.is_custom,
            version=c.version,
            updated_at=c.updated_at,
        )
        for c in configs
    ]


@router.get(
    "/{agent_id}",
    response_model=AgentConfigDetail,
    summary="Get agent configuration details",
)
async def get_agent_config(agent_id: str) -> AgentConfigDetail:
    """Get full configuration for a specific agent."""
    store = get_agent_config_store()
    config = store.get_config(agent_id)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found"
        )
    
    return AgentConfigDetail(**config.model_dump())


@router.put(
    "/{agent_id}",
    response_model=AgentConfigDetail,
    summary="Update agent configuration",
)
async def update_agent_config(
    agent_id: str,
    request: UpdateAgentConfigRequest,
) -> AgentConfigDetail:
    """
    Update an agent's prompts and LLM settings.
    
    Changes take effect immediately for new interactions.
    """
    store = get_agent_config_store()
    
    if not store.get_config(agent_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found"
        )
    
    # Build updates dict, excluding None values
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No updates provided"
        )
    
    try:
        updated = store.update_config(agent_id, updates, updated_by="api")
        return AgentConfigDetail(**updated.model_dump())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{agent_id}/reset",
    response_model=AgentConfigDetail,
    summary="Reset agent to default configuration",
)
async def reset_agent_config(agent_id: str) -> AgentConfigDetail:
    """Reset an agent's configuration to factory defaults."""
    store = get_agent_config_store()
    
    if not store.get_config(agent_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found"
        )
    
    try:
        reset = store.reset_to_default(agent_id)
        return AgentConfigDetail(**reset.model_dump())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{agent_id}/test",
    response_model=TestPromptResponse,
    summary="Test a prompt configuration",
)
async def test_agent_prompt(
    agent_id: str,
    request: TestPromptRequest,
) -> TestPromptResponse:
    """
    Test a prompt configuration with a sample input.
    
    Useful for validating prompts before saving.
    Uses the currently configured LLM provider (OpenAI or Gemini).
    """
    try:
        from datetime import datetime, timezone
        from app.api.config import get_runtime_config, LLMProvider
        from app.core.llm import CompletionRequest, GenerationConfig, ResponseFormat
        
        runtime_config = get_runtime_config()
        
        if not runtime_config.is_configured():
            return TestPromptResponse(
                success=False,
                latency_ms=0,
                error="No LLM API key configured. Add your API key in Settings."
            )
        
        # Create LLM client based on current provider
        provider = runtime_config.get_provider()
        api_key = runtime_config.get_api_key()
        
        if provider == LLMProvider.GEMINI:
            from app.integrations.gemini_client import GeminiClient, GeminiConfig
            client_config = GeminiConfig(api_key=api_key)
            client = GeminiClient(client_config)
            # Use appropriate Gemini model if OpenAI model was specified
            model = request.model
            if model.startswith("gpt"):
                model = "gemini-2.5-flash"  # Default Gemini model
        else:
            from app.integrations.openai_client import OpenAIClient, OpenAIConfig
            client_config = OpenAIConfig(api_key=api_key)
            client = OpenAIClient(client_config)
            # Use appropriate OpenAI model if Gemini model was specified
            model = request.model
            if model.startswith("gemini"):
                model = "gpt-4o-mini"  # Default OpenAI model
        
        # Build request
        completion_request = CompletionRequest(
            system_prompt=request.system_prompt,
            user_prompt=request.user_prompt,
            config=GenerationConfig(
                temperature=request.temperature,
                max_tokens=512,
                response_format=ResponseFormat.JSON,
            ),
        )
        
        start_time = datetime.now(timezone.utc)
        response = await client.complete(completion_request, model=model)
        end_time = datetime.now(timezone.utc)
        latency_ms = int((end_time - start_time).total_seconds() * 1000)
        
        if response.is_success:
            return TestPromptResponse(
                success=True,
                output=response.content,
                parsed_output=response.structured_output,
                latency_ms=latency_ms,
                tokens_used=response.usage.total_tokens if response.usage else None,
            )
        else:
            return TestPromptResponse(
                success=False,
                latency_ms=latency_ms,
                error=response.error_message or "LLM request failed",
            )
            
    except Exception as e:
        logger.error(f"Prompt test failed: {e}")
        return TestPromptResponse(
            success=False,
            latency_ms=0,
            error=str(e),
        )


@router.get(
    "/{agent_id}/history",
    summary="Get configuration change history",
)
async def get_agent_config_history(
    agent_id: str,
    limit: int = 10,
) -> List[Dict]:
    """Get history of configuration changes for an agent."""
    store = get_agent_config_store()
    
    if not store.get_config(agent_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found"
        )
    
    return store.get_history(agent_id, limit)


@router.get(
    "/schemas/output",
    summary="Get available output schemas",
)
async def get_output_schemas() -> Dict[str, Any]:
    """Get the output schema definitions for each agent type."""
    from app.agents.prompts import (
        PRIMARY_AGENT_OUTPUT_SCHEMA,
        SUPERVISOR_AGENT_OUTPUT_SCHEMA,
    )
    
    return {
        "primary": PRIMARY_AGENT_OUTPUT_SCHEMA,
        "supervisor": SUPERVISOR_AGENT_OUTPUT_SCHEMA,
        "escalation": {
            "type": "object",
            "required": ["should_escalate", "escalation_type", "reason", "priority"],
            "properties": {
                "should_escalate": {"type": "boolean"},
                "escalation_type": {
                    "type": "string",
                    "enum": ["none", "human_immediate", "human_queue", "ticket"]
                },
                "reason": {"type": "string"},
                "priority": {"type": "integer", "minimum": 1, "maximum": 5}
            }
        }
    }

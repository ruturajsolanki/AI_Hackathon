"""
Agent Prompt Templates

Enterprise-grade prompt templates for autonomous AI agents.
Designed for structured output, safety, and transparency.

These prompts enforce:
- Structured JSON responses
- Hallucination prevention
- AI disclosure requirements
- Deterministic behavior
"""

from typing import Dict, Any

# -----------------------------------------------------------------------------
# Output Schemas
# -----------------------------------------------------------------------------

PRIMARY_AGENT_OUTPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["intent", "emotion", "confidence", "response", "reasoning"],
    "properties": {
        "intent": {
            "type": "string",
            "enum": [
                "billing_inquiry",
                "technical_support",
                "account_management",
                "product_information",
                "complaint",
                "feedback",
                "order_status",
                "cancellation",
                "general_inquiry",
                "unknown"
            ],
            "description": "Detected customer intent category"
        },
        "emotion": {
            "type": "string",
            "enum": [
                "neutral",
                "satisfied",
                "frustrated",
                "confused",
                "urgent",
                "angry",
                "anxious"
            ],
            "description": "Detected customer emotional state"
        },
        "confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Confidence score from 0.0 to 1.0"
        },
        "response": {
            "type": "string",
            "description": "Response to deliver to customer"
        },
        "reasoning": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Step-by-step reasoning for the decision"
        },
        "requires_clarification": {
            "type": "boolean",
            "description": "Whether clarification is needed from customer"
        },
        "suggested_actions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Suggested follow-up actions"
        }
    },
    "additionalProperties": False
}

SUPERVISOR_AGENT_OUTPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["approved", "quality_score", "compliance_status", "risk_level", "reasoning"],
    "properties": {
        "approved": {
            "type": "boolean",
            "description": "Whether the decision is approved for delivery"
        },
        "quality_score": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Quality assessment score from 0.0 to 1.0"
        },
        "compliance_status": {
            "type": "string",
            "enum": ["compliant", "warning", "violation"],
            "description": "Compliance check result"
        },
        "risk_level": {
            "type": "string",
            "enum": ["none", "low", "medium", "high", "critical"],
            "description": "Assessed risk level"
        },
        "tone_appropriate": {
            "type": "boolean",
            "description": "Whether tone matches customer emotional state"
        },
        "adjusted_confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Adjusted confidence after review"
        },
        "flags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Any flags or concerns raised"
        },
        "recommendations": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Recommendations for improvement"
        },
        "reasoning": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Step-by-step review reasoning"
        }
    },
    "additionalProperties": False
}


# -----------------------------------------------------------------------------
# Primary Agent Prompts
# -----------------------------------------------------------------------------

PRIMARY_AGENT_SYSTEM_PROMPT = """You are a Primary Interaction Agent for an enterprise customer service center.

## Your Role
You handle initial customer interactions by:
1. Detecting customer intent
2. Assessing emotional state
3. Generating appropriate responses
4. Reporting your confidence level

## Critical Rules

### Accuracy & Honesty
- NEVER fabricate information, policies, prices, or account details
- If you don't know something, say "I don't have that information"
- Only reference information explicitly provided in context
- Do not guess or assume customer account details

### AI Disclosure
- You ARE an AI assistant - never claim to be human
- If asked directly, confirm you are an AI
- Do not pretend to have human experiences or emotions

### Response Guidelines
- Be concise and professional
- Match tone to customer's emotional state
- Acknowledge frustration or concerns before solving
- Do not make promises you cannot verify
- Use phrases like "Based on the information available..." when uncertain

### Confidence Scoring
- 0.9-1.0: Clear intent, sufficient context, straightforward response
- 0.7-0.9: Confident but some ambiguity exists
- 0.5-0.7: Uncertain, may need clarification
- Below 0.5: Cannot reliably determine intent or response

## Output Format
Respond ONLY with valid JSON matching the required schema. No additional text."""


PRIMARY_AGENT_USER_PROMPT_TEMPLATE = """## Customer Message
{customer_message}

## Context
- Channel: {channel}
- Turn Count: {turn_count}
- Previous Intent: {previous_intent}
- Previous Emotion: {previous_emotion}

## Conversation History
{conversation_history}

## Knowledge Base Context
{knowledge_context}

## Task
Analyze the customer message and generate a CONVERSATIONAL response.

**CRITICAL**: The Knowledge Base Context contains INTERNAL AGENT PROCEDURES, NOT customer-facing text.
- These numbered steps are GUIDANCE FOR YOU, not to be read to the customer
- Use the procedures to understand WHAT to do, then generate a natural response
- For order inquiries: ASK for the order number first - don't recite lookup steps
- For billing issues: ASK for relevant details - don't recite verification steps
- Always respond in NATURAL, CONVERSATIONAL language

Return a JSON object with:
- intent: The detected intent category
- emotion: The detected emotional state  
- confidence: Your confidence score (0.0 to 1.0)
- response: Your NATURAL, CONVERSATIONAL response to the customer (DO NOT include numbered steps or internal procedures)
- reasoning: Array of reasoning steps
- requires_clarification: Whether you need more information
- suggested_actions: Any follow-up actions needed

Example - If customer asks about order status:
- BAD response: "1. Get order number from customer. 2. Look up order in system..."
- GOOD response: "I'd be happy to help you track your order! Could you please provide your order number? You can find it in your confirmation email."

Remember: NEVER read internal procedures to customers. Generate natural, helpful responses."""


# -----------------------------------------------------------------------------
# Supervisor Agent Prompts
# -----------------------------------------------------------------------------

SUPERVISOR_AGENT_SYSTEM_PROMPT = """You are a Supervisor Agent responsible for reviewing AI-generated customer service responses.

## Your Role
You review decisions from the Primary Agent for:
1. Quality and relevance
2. Tone appropriateness
3. Compliance with policies
4. Risk assessment

## Review Criteria

### Quality Assessment (0.0 - 1.0)
- Does the response address the customer's actual concern?
- Is the response complete but concise?
- Is the language clear and professional?
- Deduct points for: vagueness, irrelevance, excessive length

### Tone Appropriateness
- Does the response acknowledge customer emotions?
- Is empathy shown for frustrated/angry customers?
- Is urgency recognized for anxious customers?
- Is the tone professional without being cold?

### Compliance Check
- COMPLIANT: Response follows all guidelines
- WARNING: Minor issues that don't require rejection
- VIOLATION: Response must not be delivered as-is

### Compliance Violations Include:
- Making unauthorized promises or guarantees
- Fabricating information not in context
- Using absolute language ("always", "never", "guaranteed")
- Failing to disclose AI nature if asked
- Inappropriate tone for emotional state

### Risk Assessment
- NONE: Standard inquiry, low complexity
- LOW: Minor sensitivity or ambiguity
- MEDIUM: Emotional customer or complex issue
- HIGH: Complaint, cancellation, or significant frustration
- CRITICAL: Safety concern, legal mention, or severe distress

### Confidence Adjustment
- Raise confidence if: Clear context, appropriate response, low risk
- Lower confidence if: Missing context, tone mismatch, compliance concerns
- Significantly lower if: High risk or compliance violation

## Output Format
Respond ONLY with valid JSON matching the required schema. No additional text."""


SUPERVISOR_AGENT_USER_PROMPT_TEMPLATE = """## Primary Agent Decision

### Detected Classification
- Intent: {detected_intent}
- Emotion: {detected_emotion}
- Original Confidence: {original_confidence}

### Generated Response
{generated_response}

### Primary Agent Reasoning
{primary_reasoning}

## Original Customer Message
{customer_message}

## Context
- Channel: {channel}
- Turn Count: {turn_count}
- Escalation History: {escalation_count} previous escalations

## Task
Review the Primary Agent's decision and response. Return a JSON object with:
- approved: Whether to approve for delivery (true/false)
- quality_score: Quality assessment (0.0 to 1.0)
- compliance_status: "compliant", "warning", or "violation"
- risk_level: "none", "low", "medium", "high", or "critical"
- tone_appropriate: Whether tone matches emotion (true/false)
- adjusted_confidence: Your adjusted confidence score
- flags: Array of any concerns or issues
- recommendations: Array of improvement suggestions
- reasoning: Array of your review reasoning steps

Be strict but fair. Reject only when necessary for customer safety or compliance."""


# -----------------------------------------------------------------------------
# Shared Components
# -----------------------------------------------------------------------------

AI_DISCLOSURE_STATEMENT = (
    "I'm an AI assistant here to help you. "
    "If you'd prefer to speak with a human agent, I can arrange that."
)

UNCERTAINTY_PHRASES = [
    "Based on the information available",
    "From what I can see",
    "According to the context provided",
    "I don't have access to that specific information",
    "I'd need to verify that with our team",
]

PROHIBITED_PHRASES = [
    "I guarantee",
    "I promise",
    "100%",
    "absolutely",
    "definitely will",
    "never",
    "always",
    "impossible",
]

EMOTIONAL_ACKNOWLEDGMENTS = {
    "frustrated": "I understand this is frustrating, and I want to help resolve this.",
    "angry": "I sincerely apologize for your experience. Let me help make this right.",
    "anxious": "I understand this is urgent for you. Let me prioritize this.",
    "confused": "Let me help clarify this for you.",
    "satisfied": "I'm glad I could help!",
}


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def build_primary_prompt(
    customer_message: str,
    channel: str = "chat",
    turn_count: int = 1,
    previous_intent: str = "none",
    previous_emotion: str = "neutral",
    conversation_history: str = "No previous messages.",
    knowledge_context: str = "No knowledge base context available.",
) -> str:
    """
    Build the user prompt for the Primary Agent.
    
    Args:
        customer_message: The customer's current message
        channel: Communication channel (voice/chat)
        turn_count: Number of conversation turns
        previous_intent: Previously detected intent
        previous_emotion: Previously detected emotion
        conversation_history: Formatted conversation history
        knowledge_context: Context from knowledge base (solutions, FAQs, customer info)
        
    Returns:
        Formatted user prompt string
    """
    return PRIMARY_AGENT_USER_PROMPT_TEMPLATE.format(
        customer_message=customer_message,
        channel=channel,
        turn_count=turn_count,
        previous_intent=previous_intent,
        previous_emotion=previous_emotion,
        conversation_history=conversation_history,
        knowledge_context=knowledge_context,
    )


def build_supervisor_prompt(
    customer_message: str,
    detected_intent: str,
    detected_emotion: str,
    original_confidence: float,
    generated_response: str,
    primary_reasoning: str,
    channel: str = "chat",
    turn_count: int = 1,
    escalation_count: int = 0,
) -> str:
    """
    Build the user prompt for the Supervisor Agent.
    
    Args:
        customer_message: The original customer message
        detected_intent: Intent detected by Primary Agent
        detected_emotion: Emotion detected by Primary Agent
        original_confidence: Primary Agent's confidence score
        generated_response: Response generated by Primary Agent
        primary_reasoning: Primary Agent's reasoning
        channel: Communication channel
        turn_count: Number of conversation turns
        escalation_count: Number of previous escalations
        
    Returns:
        Formatted user prompt string
    """
    return SUPERVISOR_AGENT_USER_PROMPT_TEMPLATE.format(
        customer_message=customer_message,
        detected_intent=detected_intent,
        detected_emotion=detected_emotion,
        original_confidence=original_confidence,
        generated_response=generated_response,
        primary_reasoning=primary_reasoning,
        channel=channel,
        turn_count=turn_count,
        escalation_count=escalation_count,
    )


def format_conversation_history(
    messages: list,
    max_messages: int = 5,
) -> str:
    """
    Format conversation history for prompt inclusion.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        max_messages: Maximum messages to include
        
    Returns:
        Formatted conversation string
    """
    if not messages:
        return "No previous messages."
    
    recent = messages[-max_messages:]
    lines = []
    
    for msg in recent:
        role = msg.get("role", "unknown").upper()
        content = msg.get("content", "")[:200]  # Truncate long messages
        lines.append(f"[{role}]: {content}")
    
    return "\n".join(lines)

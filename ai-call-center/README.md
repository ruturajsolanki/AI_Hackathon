# AI-Powered Digital Call Center

An enterprise-grade customer service platform powered by autonomous AI agents with built-in safety controls, transparency, and human oversight.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Responsible AI](#responsible-ai)
- [API Reference](#api-reference)
- [Interaction Lifecycle](#interaction-lifecycle)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Documentation](#documentation)

---

## Overview

This system demonstrates how autonomous AI agents can handle customer service interactions while maintaining enterprise-grade safety, compliance, and transparency standards.

### What It Does

| Capability | Description |
|------------|-------------|
| **Intent Detection** | Automatically classifies customer inquiries (billing, support, complaints, etc.) |
| **Emotion Assessment** | Detects customer emotional state to tailor responses appropriately |
| **Autonomous Resolution** | Handles routine inquiries without human intervention |
| **Smart Escalation** | Routes complex or sensitive issues to human agents |
| **Full Transparency** | Every AI decision is logged, explained, and auditable |

### Design Principles

1. **Safety First** — AI operates within strict boundaries; escalates when uncertain
2. **Human-in-the-Loop** — Humans can review, override, or intervene at any point
3. **Explainable AI** — Every decision includes reasoning that can be audited
4. **Privacy by Design** — Customer data is minimized and protected

---

## Key Features

### Multi-Agent Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Customer Interaction                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    PRIMARY AGENT                             │
│  • Detects intent and emotion                               │
│  • Generates response draft                                 │
│  • Reports confidence level                                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   SUPERVISOR AGENT                           │
│  • Reviews quality and tone                                 │
│  • Checks compliance                                        │
│  • Adjusts confidence                                       │
│  • Approves or flags for escalation                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   ESCALATION AGENT                           │
│  • Evaluates escalation triggers                            │
│  • Determines routing (human, ticket, retry)                │
│  • Generates handoff context                                │
└─────────────────────────┴───────────────────────────────────┘
```

### Confidence-Based Autonomy

| Confidence Level | Score Range | System Behavior |
|-----------------|-------------|-----------------|
| **High** | ≥ 0.7 | Autonomous handling |
| **Medium** | 0.5 – 0.7 | Supervisor review required |
| **Low** | < 0.5 | Escalation to human |

### Enterprise Controls

- **Audit Logging** — Complete decision trail for compliance
- **Safety Guards** — Prohibited phrases and sensitive topics trigger review
- **Graceful Degradation** — Falls back to safe defaults if AI fails

---

## Architecture

```
ai-call-center/
├── backend/
│   └── app/
│       ├── agents/           # AI agent implementations
│       │   ├── primary.py    # Customer-facing agent
│       │   ├── supervisor.py # Quality & compliance review
│       │   ├── escalation.py # Routing decisions
│       │   └── prompts.py    # LLM prompt templates
│       ├── api/              # REST API endpoints
│       ├── core/             # Configuration & models
│       ├── analytics/        # Metrics & audit logging
│       ├── memory/           # Context management
│       ├── services/         # Orchestration
│       └── integrations/     # External services (LLM, voice)
├── frontend/                 # React dashboard
└── docs/                     # Design documentation
```

---

## Responsible AI

### How AI is Used

| Component | AI Role | Human Oversight |
|-----------|---------|-----------------|
| Intent Detection | LLM classifies customer intent | Supervisor validates accuracy |
| Response Generation | LLM drafts responses | Supervisor reviews tone/compliance |
| Confidence Scoring | Deterministic rules evaluate certainty | Thresholds trigger human review |
| Escalation | Rule-based triggers, never bypassed | Humans handle all escalations |

### Safety Guarantees

**These rules are NEVER overridden by AI:**

1. **Sensitive Topics** — Legal, medical, harassment mentions always escalate
2. **Prohibited Phrases** — "Guarantee", "promise", "100%" trigger rejection
3. **Compliance Violations** — Policy breaches block response delivery
4. **Critical Risk** — Caps AI confidence at 30%, requires human

### AI Disclosure

The system is designed to be transparent:

- AI confirms its nature if asked
- Never claims to be human
- Uses phrases like "Based on the information available..." for uncertainty
- Every decision includes reasoning steps

### Fallback Behavior

If the LLM is unavailable or fails:

1. System uses deterministic keyword-based analysis
2. Confidence is automatically reduced by 15%
3. Conservative defaults apply (reject rather than approve)
4. Human escalation is triggered for complex cases

---

## API Reference

### Base URL

```
http://localhost:8000/api
```

### Endpoints

#### Start Interaction

```http
POST /api/interactions/start
Content-Type: application/json

{
  "customer_id": "cust_12345",
  "channel": "chat",
  "initial_message": "I need help with my bill"
}
```

**Response:**

```json
{
  "interaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "in_progress",
  "channel": "chat",
  "started_at": "2026-01-18T10:30:00Z",
  "initial_response": "I can help you with your billing inquiry...",
  "should_escalate": false
}
```

#### Send Message

```http
POST /api/interactions/{interaction_id}/message
Content-Type: application/json

{
  "content": "Why was I charged $50 extra?"
}
```

**Response:**

```json
{
  "interaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "message_processed": true,
  "response_content": "I understand you're concerned about the additional charge...",
  "should_escalate": false,
  "confidence_level": "high",
  "processing_time_ms": 1250
}
```

#### End Interaction

```http
POST /api/interactions/{interaction_id}/end
```

**Response:**

```json
{
  "interaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "resolved",
  "total_turns": 4,
  "was_escalated": false,
  "duration_seconds": 180.5,
  "resolution_type": "ai_resolved"
}
```

#### Health Check

```http
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2026-01-18T10:30:00Z",
  "version": "0.1.0"
}
```

---

## Interaction Lifecycle

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         INTERACTION LIFECYCLE                             │
└──────────────────────────────────────────────────────────────────────────┘

1. INITIATION
   ├─ Customer sends message
   ├─ System creates interaction context
   └─ Audit: INTERACTION_STARTED

2. PRIMARY PROCESSING
   ├─ Primary Agent analyzes message
   │   ├─ Detect intent (billing, support, complaint...)
   │   ├─ Assess emotion (neutral, frustrated, angry...)
   │   └─ Generate response draft
   ├─ Calculate confidence score
   └─ Audit: PRIMARY_DECISION

3. SUPERVISOR REVIEW
   ├─ Supervisor Agent reviews decision
   │   ├─ Quality check (relevance, completeness)
   │   ├─ Tone check (matches customer emotion)
   │   ├─ Compliance check (no prohibited content)
   │   └─ Risk assessment
   ├─ Adjust confidence if needed
   ├─ Approve or reject
   └─ Audit: SUPERVISOR_REVIEW

4. ESCALATION EVALUATION
   ├─ Escalation Agent evaluates triggers
   │   ├─ Confidence below threshold?
   │   ├─ Compliance violation?
   │   ├─ High risk situation?
   │   └─ Customer explicitly requested human?
   ├─ Determine routing (if escalating)
   └─ Audit: ESCALATION_DECISION

5. RESPONSE DELIVERY
   ├─ If approved: deliver AI response
   ├─ If rejected: provide fallback message
   └─ If escalated: connect to human agent

6. COMPLETION
   ├─ Interaction resolved or escalated
   ├─ Analytics recorded
   └─ Audit: INTERACTION_ENDED
```

### Decision Flow

```
                    ┌─────────────────┐
                    │ Primary Agent   │
                    │ Confidence: 0.82│
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Supervisor      │
                    │ Approved: Yes   │
                    │ Adjusted: 0.78  │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
     ┌────────▼────────┐           ┌────────▼────────┐
     │ Confidence ≥ 0.7│           │ Confidence < 0.7│
     │ → Respond       │           │ → Escalate      │
     └─────────────────┘           └─────────────────┘
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- OpenAI API key (optional for demo mode)

### Quick Start

```bash
# Clone and navigate
cd ai-call-center

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure (optional - works without for demo)
export OPENAI_API_KEY=sk-your-key-here

# Run backend
uvicorn app.main:app --reload --port 8000

# Frontend setup (new terminal)
cd ../frontend
npm install
npm run dev
```

### Running Without API Key

The system can run in demo mode without an OpenAI API key:

```bash
# Use mock LLM for demos
export LLM_USE_MOCK=true
uvicorn app.main:app --reload
```

In mock mode:
- Uses keyword-based intent/emotion detection
- Generates template-based responses
- All safety and escalation rules still apply

### API Documentation

Once running, access the interactive API docs:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Configuration

### Environment Variables

```bash
# Application
ENVIRONMENT=development    # development, staging, production
DEBUG=true

# LLM Configuration
OPENAI_API_KEY=sk-...      # Required for AI features
LLM_USE_MOCK=false         # Set true for demo without API key
LLM_PROVIDER=openai        # openai, anthropic, mock

# Agent Behavior
AGENT_AUTONOMOUS_THRESHOLD=0.7
AGENT_SUPERVISION_THRESHOLD=0.5
AGENT_ESCALATION_THRESHOLD=0.4

# Audit & Compliance
AUDIT_ENABLED=true
AUDIT_LOG_DECISIONS=true
```

### Confidence Thresholds

| Setting | Default | Effect |
|---------|---------|--------|
| `AGENT_AUTONOMOUS_THRESHOLD` | 0.7 | Above: AI handles independently |
| `AGENT_SUPERVISION_THRESHOLD` | 0.5 | 0.5-0.7: Requires supervisor approval |
| `AGENT_ESCALATION_THRESHOLD` | 0.4 | Below: Escalates to human |

---

## Documentation

Detailed design documentation is available in the `docs/` folder:

| Document | Description |
|----------|-------------|
| `ARCHITECTURE.md` | System architecture and layers |
| `AGENT_INTERACTION_FLOW.md` | How agents collaborate |
| `AI_DECISION_FRAMEWORK.md` | Decision-making philosophy |
| `CONFIDENCE_CONTROL_SYSTEM.md` | How confidence governs autonomy |
| `SAFETY_RISK_ANALYSIS.md` | Failure modes and mitigations |
| `API_CONTRACTS.md` | API specifications |
| `SERVICE_BOUNDARIES.md` | Service decomposition |
| `ETHICS_BASELINE.md` | Ethical guidelines |

---

## License

This project was created for demonstration purposes.

---

## Contact

For questions about this implementation, please refer to the documentation or open an issue.

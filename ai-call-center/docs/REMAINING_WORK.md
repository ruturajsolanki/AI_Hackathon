# Remaining Work

## AI-Powered Digital Call Center - Deferred Features & Future Roadmap

**Document Version:** 1.0.0  
**Last Updated:** January 2026

---

## Overview

This document outlines features that have been **intentionally deferred** from the MVP implementation. Each item includes rationale for deferral, implementation approach, and affected components.

---

## 1. Authentication & Multi-Tenancy

### Why Deferred

- MVP focuses on demonstrating AI capabilities
- Auth implementation varies significantly by enterprise requirements
- Adds complexity that obscures core functionality for demos/judges

### Implementation Plan

**Phase 1: API Authentication**
```
Components Affected:
- app/api/*  (all endpoints)
- app/core/config.py
- app/main.py

Approach:
1. Add JWT-based authentication middleware
2. Create /auth/login and /auth/refresh endpoints
3. Add Bearer token validation to all routes
4. Store sessions in Redis

Dependencies:
- python-jose[cryptography]
- passlib[bcrypt]
- Redis for session storage
```

**Phase 2: Multi-Tenancy**
```
Components Affected:
- app/persistence/store.py
- app/memory/context_store.py
- app/analytics/metrics.py
- All database queries

Approach:
1. Add organization_id to all entities
2. Implement row-level security
3. Add tenant context to all requests
4. Isolate analytics per organization
```

### Estimated Effort

- Authentication: 2-3 days
- Multi-tenancy: 4-5 days

---

## 2. Billing & Usage Tracking

### Why Deferred

- Requires integration with payment providers
- Complex metering logic for AI token usage
- Outside scope of AI/agent demonstration

### Implementation Plan

```
New Components:
- app/billing/
  - metering.py       # Track token/interaction usage
  - subscription.py   # Subscription tier management
  - invoice.py        # Invoice generation

Approach:
1. Create usage metering middleware
2. Track LLM token consumption per tenant
3. Integrate with Stripe/equivalent for payments
4. Build usage dashboard in frontend

APIs:
- GET  /api/billing/usage          # Current period usage
- GET  /api/billing/invoices       # Invoice history
- POST /api/billing/subscription   # Manage subscription
```

### Estimated Effort

- Metering infrastructure: 2 days
- Payment integration: 3-4 days
- Frontend dashboard: 2 days

---

## 3. Phone Call (PSTN) Integration

### Why Deferred

- Requires telephony provider contracts (Twilio, etc.)
- Involves real-time audio processing
- Significant infrastructure complexity
- Current browser-based voice is sufficient for demo

### Implementation Plan

```
New Components:
- app/integrations/telephony/
  - twilio_client.py    # Twilio integration
  - sip_handler.py      # SIP protocol handling
  - media_stream.py     # Real-time audio streaming

Approach:
1. Set up Twilio/equivalent account
2. Implement WebSocket media streaming
3. Create real-time STT/TTS pipeline
4. Handle call state machine (ringing, connected, hold, transfer)
5. Add IVR menu support

Infrastructure:
- Media server for audio processing
- WebRTC gateway
- SIP trunking

APIs:
- POST /api/calls/inbound    # Handle incoming calls
- POST /api/calls/outbound   # Initiate outbound calls
- POST /api/calls/{id}/transfer  # Transfer to human
```

### Estimated Effort

- Basic Twilio integration: 1 week
- Full call center features: 2-3 weeks

---

## 4. Prompt Editing UI

### Why Deferred

- Exposing prompts has security/IP implications
- Requires careful access control
- Could lead to unexpected AI behaviors
- Demo should show curated experience

### Implementation Plan

```
New Components:
- Frontend: components/prompts/
  - PromptEditor.tsx
  - PromptVersionHistory.tsx
  - PromptTestBench.tsx
  
- Backend: app/api/prompts.py

Approach:
1. Store prompts in database with versioning
2. Create admin-only prompt management UI
3. Implement A/B testing framework
4. Add prompt validation before deployment

Security Considerations:
- Admin-only access
- Audit all prompt changes
- Validate prompts don't bypass safety rules
- Require approval workflow for production
```

### Estimated Effort

- Backend prompt management: 2 days
- Frontend editor: 3 days
- A/B testing framework: 2 days

---

## 5. Model Switching UI

### Why Deferred

- Requires multiple LLM provider integrations
- Cost implications of different models
- Needs careful evaluation framework
- Demo uses single optimized configuration

### Implementation Plan

```
Components Affected:
- app/core/llm.py
- app/integrations/
  - anthropic_client.py  (new)
  - azure_client.py      (new)
- Frontend: components/settings/ModelSettings.tsx

Approach:
1. Implement additional LLMClient providers
2. Create model registry with capabilities
3. Build comparison/evaluation framework
4. Add per-agent model configuration
5. Implement fallback chains

APIs:
- GET  /api/config/models           # Available models
- POST /api/config/models/{agent}   # Set model for agent
- GET  /api/config/models/costs     # Cost estimates
```

### Estimated Effort

- Additional providers: 1 day each
- Model registry: 1 day
- Frontend UI: 2 days

---

## 6. Human Agent Interface

### Why Deferred

- Requires WebSocket-based real-time UI
- Complex state management for handoffs
- Needs CRM integration
- Demo focuses on AI autonomy

### Implementation Plan

```
New Components:
- Frontend: components/agent-portal/
  - AgentQueue.tsx         # Incoming escalations
  - AgentWorkspace.tsx     # Active conversation view
  - CustomerHistory.tsx    # Past interactions
  - QuickResponses.tsx     # Template responses

- Backend: app/api/agent_portal.py

Approach:
1. Create dedicated agent authentication
2. Build real-time escalation queue
3. Implement conversation takeover
4. Add typing indicators and presence
5. Build internal notes system
6. Create return-to-AI workflow

WebSocket Events:
- escalation:new
- escalation:accepted
- customer:message
- agent:typing
- handback:complete
```

### Estimated Effort

- Backend agent APIs: 3 days
- Real-time infrastructure: 2 days
- Frontend portal: 1 week

---

## 7. Advanced Analytics

### Why Deferred

- Requires significant data accumulation
- ML-based insights need training data
- Current analytics sufficient for demo

### Implementation Plan

```
New Components:
- app/analytics/
  - ml_insights.py         # ML-based predictions
  - anomaly_detection.py   # Unusual patterns
  - sentiment_trends.py    # Customer sentiment over time
  
- Frontend: components/analytics/
  - PredictiveInsights.tsx
  - AnomalyAlerts.tsx
  - SentimentDashboard.tsx

Features:
1. Call volume prediction
2. Customer churn risk scoring
3. Agent performance optimization
4. Peak time identification
5. Topic trending analysis
```

### Estimated Effort

- ML pipeline setup: 1 week
- Dashboard components: 4-5 days

---

## 8. Webhook Notifications

### Why Deferred

- Requires external endpoint configuration
- Security considerations for outbound calls
- Nice-to-have for enterprise integration

### Implementation Plan

```
New Components:
- app/webhooks/
  - dispatcher.py      # Send webhook events
  - retry_queue.py     # Handle failures
  - signatures.py      # Request signing

APIs:
- POST /api/webhooks              # Register webhook
- GET  /api/webhooks              # List webhooks
- DELETE /api/webhooks/{id}       # Remove webhook

Events:
- interaction.started
- interaction.completed
- interaction.escalated
- agent.decision
- compliance.violation
```

### Estimated Effort

- Webhook infrastructure: 2-3 days
- Frontend management UI: 1 day

---

## 9. Custom Agent Behaviors

### Why Deferred

- Requires safe execution environment
- Potential security risks
- Complex testing requirements
- Demo uses proven configurations

### Implementation Plan

```
Approach:
1. Create agent behavior DSL or scripting
2. Implement sandboxed execution
3. Build behavior testing framework
4. Add version control for behaviors
5. Create approval workflow

Considerations:
- Cannot bypass safety rules
- Must maintain audit logging
- Rate limited execution
- Rollback capability
```

### Estimated Effort

- DSL design: 1 week
- Safe execution: 3-4 days
- Testing framework: 2-3 days

---

## 10. Database Migration (SQLite → PostgreSQL)

### Why Deferred

- SQLite sufficient for demo/MVP
- PostgreSQL adds operational complexity
- Can be done transparently later

### Implementation Plan

```
Steps:
1. Update app/persistence/store.py for PostgreSQL
2. Create Alembic migration scripts
3. Add connection pooling (asyncpg)
4. Update Docker compose for PostgreSQL
5. Create data migration script

Dependencies:
- asyncpg
- sqlalchemy[asyncio]
- alembic
```

### Estimated Effort

- Implementation: 1-2 days
- Testing: 1 day

---

## Priority Matrix

| Feature | Business Value | Implementation Effort | Priority |
|---------|---------------|----------------------|----------|
| Authentication | High | Medium | P1 |
| PostgreSQL Migration | Medium | Low | P1 |
| Human Agent Interface | High | High | P2 |
| Phone Integration | High | Very High | P2 |
| Billing | Medium | Medium | P2 |
| Advanced Analytics | Medium | High | P3 |
| Prompt Editing | Low | Medium | P3 |
| Model Switching | Low | Medium | P3 |
| Webhooks | Low | Low | P3 |
| Custom Behaviors | Low | Very High | P4 |

---

## Summary

The current MVP provides a **fully functional AI call center** with:
- ✅ Autonomous AI agents with confidence-based decisions
- ✅ Real-time voice and chat support
- ✅ Comprehensive analytics and audit logging
- ✅ Secure runtime API key configuration
- ✅ Enterprise-grade architecture

Deferred features are documented here for future implementation as the product scales beyond demo/MVP stage.

---

*Document maintained by the engineering team*

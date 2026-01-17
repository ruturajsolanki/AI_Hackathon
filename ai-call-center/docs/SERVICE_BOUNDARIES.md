# Service Boundaries

## AI-Powered Digital Call Center Using Autonomous AI Agents

**Document Version:** 1.0  
**Date:** January 17, 2026  
**Phase:** 4 — API & Backend Design  
**Alignment:** Architecture defined in `ARCHITECTURE.md` and agent model in `AGENT_INTERACTION_FLOW.md`  

---

## 1. Service Decomposition Philosophy

### 1.1 Design Principles

The backend is decomposed into services following these principles:

| Principle | Application |
|-----------|-------------|
| **Single Responsibility** | Each service owns one coherent domain |
| **Loose Coupling** | Services interact through defined contracts, not internal knowledge |
| **High Cohesion** | Related functionality stays together |
| **Autonomous Operation** | Services can function independently during partial failures |
| **Scalability Aligned** | Services scale based on their specific load characteristics |

### 1.2 Decomposition Rationale

Services are separated along **domain boundaries**, not technical layers:

```
┌─────────────────────────────────────────────────────────────────┐
│                 SERVICE DOMAIN MAP                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CUSTOMER INTERACTION DOMAIN                                     │
│  └── Conversation Service                                        │
│  └── Channel Gateway Service                                     │
│                                                                  │
│  SESSION MANAGEMENT DOMAIN                                       │
│  └── Session Service                                             │
│  └── Routing Service                                             │
│                                                                  │
│  AI AGENT DOMAIN                                                 │
│  └── Primary Agent Service                                       │
│  └── Supervisor Service                                          │
│  └── Escalation Service                                          │
│                                                                  │
│  KNOWLEDGE & DATA DOMAIN                                         │
│  └── Knowledge Service                                           │
│  └── Customer Profile Service                                    │
│  └── Context Service                                             │
│                                                                  │
│  OPERATIONS DOMAIN                                               │
│  └── Analytics Service                                           │
│  └── Audit Service                                               │
│                                                                  │
│  INTEGRATION DOMAIN                                              │
│  └── Enterprise Gateway Service                                  │
│  └── AI Provider Service                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Backend Services

### Service Overview

| # | Service | Domain | Purpose |
|---|---------|--------|---------|
| 1 | Channel Gateway Service | Interaction | Manages communication channels |
| 2 | Conversation Service | Interaction | Orchestrates conversation flow |
| 3 | Session Service | Session Management | Manages session lifecycle |
| 4 | Routing Service | Session Management | Assigns and routes sessions |
| 5 | Primary Agent Service | AI Agent | Executes customer-facing AI |
| 6 | Supervisor Service | AI Agent | Monitors AI quality |
| 7 | Escalation Service | AI Agent | Handles human handoff |
| 8 | Knowledge Service | Knowledge & Data | Manages knowledge retrieval |
| 9 | Customer Profile Service | Knowledge & Data | Manages customer data |
| 10 | Context Service | Knowledge & Data | Manages conversation context |
| 11 | Analytics Service | Operations | Collects metrics and events |
| 12 | Audit Service | Operations | Maintains audit trail |
| 13 | Enterprise Gateway Service | Integration | Connects to enterprise systems |
| 14 | AI Provider Service | Integration | Manages AI model access |

---

## 3. Service Specifications

### 3.1 Channel Gateway Service

#### Identity

| Attribute | Value |
|-----------|-------|
| **Domain** | Customer Interaction |
| **Scaling Trigger** | Concurrent connections |
| **Stateful** | Connection state only |

#### Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Accept connections | Establish and maintain client connections (voice, chat) |
| Protocol handling | Manage channel-specific protocols |
| Audio streaming | Handle real-time audio input/output for voice channel |
| Message queuing | Queue inbound/outbound messages for chat channel |
| Connection health | Monitor and manage connection lifecycle |
| Channel adaptation | Normalize input/output for downstream processing |

#### Does NOT Handle

| Exclusion | Handled By |
|-----------|------------|
| Understanding message content | Conversation Service |
| Session creation or management | Session Service |
| AI processing | Primary Agent Service |
| Speech-to-text / text-to-speech | AI Provider Service |
| Business logic | Primary Agent Service |
| Authentication | Session Service |

---

### 3.2 Conversation Service

#### Identity

| Attribute | Value |
|-----------|-------|
| **Domain** | Customer Interaction |
| **Scaling Trigger** | Active conversations |
| **Stateful** | No (references Session Service) |

#### Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Orchestrate conversation | Coordinate turn-taking between customer and AI |
| Invoke AI agent | Request responses from Primary Agent Service |
| Apply guardrails | Ensure AI responses pass safety checks before delivery |
| Handle turn management | Manage conversation flow and interruptions |
| Coordinate I/O | Bridge Channel Gateway with AI Agent services |
| Manage response timing | Ensure responses delivered within latency budget |

#### Does NOT Handle

| Exclusion | Handled By |
|-----------|------------|
| Generating AI responses | Primary Agent Service |
| Session lifecycle | Session Service |
| Channel protocols | Channel Gateway Service |
| Knowledge retrieval | Knowledge Service |
| Context storage | Context Service |
| Escalation execution | Escalation Service |

---

### 3.3 Session Service

#### Identity

| Attribute | Value |
|-----------|-------|
| **Domain** | Session Management |
| **Scaling Trigger** | Active sessions |
| **Stateful** | Session state ownership |

#### Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Create sessions | Initialize new customer sessions |
| Track session state | Maintain session status (active, escalated, closed) |
| Manage session lifecycle | Handle session start, suspend, resume, end |
| Authentication context | Maintain customer authentication state |
| Session recovery | Restore sessions after transient failures |
| Session timeout | End inactive sessions appropriately |

#### Does NOT Handle

| Exclusion | Handled By |
|-----------|------------|
| Routing decisions | Routing Service |
| Conversation content | Conversation Service, Context Service |
| AI agent assignment | Routing Service |
| Customer profile data | Customer Profile Service |
| Escalation logic | Escalation Service |

---

### 3.4 Routing Service

#### Identity

| Attribute | Value |
|-----------|-------|
| **Domain** | Session Management |
| **Scaling Trigger** | Routing requests |
| **Stateful** | No |

#### Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Assign AI agents | Route new sessions to available AI agent instances |
| Load balancing | Distribute load across AI agent pool |
| Queue management | Manage waiting sessions if capacity constrained |
| Priority handling | Apply priority rules for different session types |
| Escalation routing | Route escalated sessions to human agents |
| Capacity monitoring | Track available capacity across agent pools |

#### Does NOT Handle

| Exclusion | Handled By |
|-----------|------------|
| Session creation | Session Service |
| Conversation handling | Conversation Service |
| Escalation decision | Primary Agent Service, Supervisor Service |
| Agent behavior | Primary Agent Service |
| Human agent management | External human agent system |

---

### 3.5 Primary Agent Service

#### Identity

| Attribute | Value |
|-----------|-------|
| **Domain** | AI Agent |
| **Scaling Trigger** | Concurrent conversations |
| **Stateful** | Conversation context reference |

#### Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Intent recognition | Understand customer intent from input |
| Response generation | Generate appropriate responses |
| Confidence assessment | Evaluate certainty of understanding and action |
| Workflow execution | Execute business workflows (lookup, booking, etc.) |
| Emotion detection | Assess customer emotional state |
| Context integration | Incorporate conversation history and customer profile |
| Escalation signaling | Determine when escalation is needed |

#### Does NOT Handle

| Exclusion | Handled By |
|-----------|------------|
| Channel management | Channel Gateway Service |
| Session lifecycle | Session Service |
| Knowledge storage | Knowledge Service |
| Quality monitoring | Supervisor Service |
| Escalation execution | Escalation Service |
| AI model invocation | AI Provider Service |
| Audit logging | Audit Service |

---

### 3.6 Supervisor Service

#### Identity

| Attribute | Value |
|-----------|-------|
| **Domain** | AI Agent |
| **Scaling Trigger** | Active sessions being monitored |
| **Stateful** | No |

#### Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Quality monitoring | Observe AI agent interactions for quality issues |
| Policy compliance | Verify responses comply with business policies |
| Intervention signaling | Send advisories to Primary Agent when needed |
| Escalation override | Force escalation when necessary |
| Pattern detection | Identify concerning patterns in conversations |
| Threshold monitoring | Watch for confidence/sentiment threshold breaches |

#### Does NOT Handle

| Exclusion | Handled By |
|-----------|------------|
| Customer interaction | Primary Agent Service |
| Response generation | Primary Agent Service |
| Escalation execution | Escalation Service |
| Session management | Session Service |
| Blocking conversation flow | Operates asynchronously |

---

### 3.7 Escalation Service

#### Identity

| Attribute | Value |
|-----------|-------|
| **Domain** | AI Agent |
| **Scaling Trigger** | Escalation events |
| **Stateful** | No |

#### Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Context compilation | Prepare conversation summary for human agent |
| Agent matching | Identify appropriate human agent for escalation |
| Handoff coordination | Manage transfer from AI to human agent |
| Context delivery | Deliver context package to human agent interface |
| Escalation tracking | Track escalation status and outcome |
| Priority classification | Assign priority level to escalations |

#### Does NOT Handle

| Exclusion | Handled By |
|-----------|------------|
| Escalation decision | Primary Agent Service, Supervisor Service |
| Customer communication during transfer | Conversation Service |
| Human agent management | External human agent system |
| Routing to human | Routing Service |
| Conversation continuation | Human agent system |

---

### 3.8 Knowledge Service

#### Identity

| Attribute | Value |
|-----------|-------|
| **Domain** | Knowledge & Data |
| **Scaling Trigger** | Query volume |
| **Stateful** | No (reads from knowledge store) |

#### Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Knowledge retrieval | Find relevant information for queries |
| Semantic search | Match queries to knowledge by meaning |
| Content ranking | Rank results by relevance |
| Source tracking | Identify source of each knowledge item |
| Freshness management | Track and communicate content currency |
| Knowledge indexing | Maintain searchable index of knowledge base |

#### Does NOT Handle

| Exclusion | Handled By |
|-----------|------------|
| Response generation | Primary Agent Service |
| Knowledge creation | Content management (external) |
| Customer-specific data | Customer Profile Service |
| Conversation context | Context Service |
| Decision making | Primary Agent Service |

---

### 3.9 Customer Profile Service

#### Identity

| Attribute | Value |
|-----------|-------|
| **Domain** | Knowledge & Data |
| **Scaling Trigger** | Profile queries |
| **Stateful** | No (reads/writes to profile store) |

#### Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Profile retrieval | Fetch customer profile by identifier |
| Profile updates | Update customer information as authorized |
| History access | Provide customer interaction history |
| Preference management | Store and retrieve customer preferences |
| Identity resolution | Match customer identifiers to profiles |
| Data protection | Enforce access controls on customer data |

#### Does NOT Handle

| Exclusion | Handled By |
|-----------|------------|
| Authentication | Session Service |
| Conversation context | Context Service |
| Knowledge content | Knowledge Service |
| Decision making | Primary Agent Service |
| Profile creation | External customer systems |

---

### 3.10 Context Service

#### Identity

| Attribute | Value |
|-----------|-------|
| **Domain** | Knowledge & Data |
| **Scaling Trigger** | Active conversations |
| **Stateful** | No (manages external state store) |

#### Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Context storage | Store conversation context during session |
| Context retrieval | Provide context for AI agent processing |
| Turn management | Track conversation turns and history |
| Goal tracking | Maintain customer goal and resolution progress |
| Context summarization | Create summaries for long conversations |
| Context expiration | Clean up context after session ends |

#### Does NOT Handle

| Exclusion | Handled By |
|-----------|------------|
| Persistent customer data | Customer Profile Service |
| Knowledge content | Knowledge Service |
| Response generation | Primary Agent Service |
| Session management | Session Service |
| Long-term storage | Audit Service (for audit purposes) |

---

### 3.11 Analytics Service

#### Identity

| Attribute | Value |
|-----------|-------|
| **Domain** | Operations |
| **Scaling Trigger** | Event volume |
| **Stateful** | No |

#### Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Event collection | Receive events from all services |
| Metrics calculation | Compute operational metrics |
| Aggregation | Aggregate data for dashboards |
| Alerting | Trigger alerts based on thresholds |
| Trend analysis | Identify patterns over time |
| Dashboard data | Provide data for operational dashboards |

#### Does NOT Handle

| Exclusion | Handled By |
|-----------|------------|
| Audit trail (compliance) | Audit Service |
| Real-time conversation flow | Conversation Service |
| Decision making | All agent services |
| Taking action on insights | Operations teams (external) |

---

### 3.12 Audit Service

#### Identity

| Attribute | Value |
|-----------|-------|
| **Domain** | Operations |
| **Scaling Trigger** | Audit event volume |
| **Stateful** | No (writes to audit store) |

#### Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Audit logging | Create immutable audit records |
| Decision logging | Record AI decisions with reasoning |
| Compliance records | Maintain records for regulatory requirements |
| Audit retrieval | Support investigation and review queries |
| Data integrity | Ensure audit records cannot be modified |
| Retention management | Manage audit data lifecycle |

#### Does NOT Handle

| Exclusion | Handled By |
|-----------|------------|
| Real-time metrics | Analytics Service |
| Alerting | Analytics Service |
| Taking action on audits | Compliance teams (external) |
| Conversation content storage | Context Service (during session) |

---

### 3.13 Enterprise Gateway Service

#### Identity

| Attribute | Value |
|-----------|-------|
| **Domain** | Integration |
| **Scaling Trigger** | Integration request volume |
| **Stateful** | No |

#### Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Enterprise abstraction | Provide unified interface to enterprise systems |
| Protocol translation | Convert between internal and enterprise formats |
| Connection management | Manage connections to enterprise systems |
| Error handling | Handle enterprise system errors gracefully |
| Retry logic | Implement retry for transient failures |
| Mock support | Provide mock responses for demo/testing |

#### Does NOT Handle

| Exclusion | Handled By |
|-----------|------------|
| Business logic | Primary Agent Service |
| Decision making | Primary Agent Service |
| Enterprise system internals | External enterprise systems |
| AI model access | AI Provider Service |

---

### 3.14 AI Provider Service

#### Identity

| Attribute | Value |
|-----------|-------|
| **Domain** | Integration |
| **Scaling Trigger** | AI request volume |
| **Stateful** | No |

#### Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Model abstraction | Provide unified interface to AI capabilities |
| LLM invocation | Call language models for response generation |
| Speech processing | Coordinate speech-to-text and text-to-speech |
| Embedding generation | Generate embeddings for semantic search |
| Rate management | Manage API rate limits and quotas |
| Fallback handling | Switch to fallback providers if primary fails |

#### Does NOT Handle

| Exclusion | Handled By |
|-----------|------------|
| Prompt construction | Primary Agent Service |
| Response interpretation | Primary Agent Service |
| Knowledge retrieval | Knowledge Service |
| Decision logic | Primary Agent Service |
| Enterprise integrations | Enterprise Gateway Service |

---

## 4. Service Communication

### 4.1 Communication Patterns

| Pattern | Use Case | Characteristics |
|---------|----------|-----------------|
| **Synchronous Request-Response** | When caller needs immediate answer | Blocking; timeout-bounded; retry on failure |
| **Asynchronous Event** | When caller doesn't need immediate response | Non-blocking; fire-and-forget; eventual processing |
| **Asynchronous Request-Reply** | When response needed but not immediately | Non-blocking; correlated response; queue-based |
| **Streaming** | Real-time data flow | Continuous; bidirectional; low-latency |

### 4.2 Service Communication Matrix

| From Service | To Service | Pattern | Rationale |
|--------------|------------|---------|-----------|
| Channel Gateway | Conversation | Streaming | Real-time conversation flow |
| Conversation | Primary Agent | Sync Request-Response | Response needed for customer |
| Conversation | Session | Sync Request-Response | Session state needed immediately |
| Primary Agent | Knowledge | Sync Request-Response | Information needed for response |
| Primary Agent | Context | Sync Request-Response | Context needed for response |
| Primary Agent | Customer Profile | Sync Request-Response | Profile needed for personalization |
| Primary Agent | Enterprise Gateway | Sync Request-Response | Business data needed for action |
| Primary Agent | AI Provider | Sync Request-Response | AI response needed |
| Primary Agent | Supervisor | Async Event | Non-blocking quality signal |
| Supervisor | Primary Agent | Async Event | Advisory, non-blocking |
| Primary Agent | Escalation | Async Request-Reply | Initiate escalation |
| Escalation | Routing | Sync Request-Response | Need human assignment |
| All Services | Analytics | Async Event | Metrics collection, non-blocking |
| All Services | Audit | Async Event | Audit logging, non-blocking |

### 4.3 Communication Visualization

```
┌─────────────────────────────────────────────────────────────────┐
│              SERVICE COMMUNICATION FLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  SYNCHRONOUS (Blocking, Immediate Response Needed)              │
│                                                                  │
│  Channel Gateway ───────► Conversation ───────► Primary Agent   │
│                                │                     │          │
│                                ▼                     ▼          │
│                            Session          ┌───────────────┐   │
│                                             │ Knowledge     │   │
│                                             │ Context       │   │
│                                             │ Profile       │   │
│                                             │ Enterprise GW │   │
│                                             │ AI Provider   │   │
│                                             └───────────────┘   │
│                                                                  │
│  ASYNCHRONOUS (Non-Blocking, Eventually Processed)              │
│                                                                  │
│  Primary Agent ─ ─ ─ ─ ─► Supervisor ─ ─ ─ ─► Primary Agent    │
│       │                       (Advisory)                        │
│       │                                                          │
│       └─ ─ ─ ─ ─► Escalation ───────► Routing                   │
│                    (When triggered)                              │
│                                                                  │
│  All Services ─ ─ ─ ─ ─► Analytics                              │
│  All Services ─ ─ ─ ─ ─► Audit                                  │
│                                                                  │
│  LEGEND: ─────► Synchronous    ─ ─ ─► Asynchronous              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.4 Synchronous Communication Requirements

| Requirement | Specification |
|-------------|---------------|
| **Timeout** | All synchronous calls have defined timeouts |
| **Retry** | Failed calls retried with exponential backoff |
| **Circuit Breaker** | Repeated failures trigger circuit breaker |
| **Fallback** | Fallback response when service unavailable |
| **Correlation** | All requests carry correlation ID for tracing |

### 4.5 Asynchronous Communication Requirements

| Requirement | Specification |
|-------------|---------------|
| **Delivery Guarantee** | At-least-once delivery |
| **Idempotency** | Receivers handle duplicate messages |
| **Ordering** | Order preserved within session scope |
| **Persistence** | Messages persisted until acknowledged |
| **Dead Letter** | Failed messages routed for investigation |

---

## 5. Why This Decomposition Supports Scalability and Autonomy

### 5.1 Scalability Benefits

#### Independent Scaling

Each service scales based on its own load characteristics:

| Service | Scaling Dimension | Why Independent |
|---------|-------------------|-----------------|
| Channel Gateway | Connections | Connection capacity ≠ AI processing capacity |
| Primary Agent | Conversations | AI processing is most resource-intensive |
| Knowledge | Queries | Read-heavy; scales differently than write |
| Analytics | Events | Batch processing; different pattern than real-time |
| AI Provider | API calls | External rate limits; separate management |

#### Bottleneck Isolation

Separating services prevents one bottleneck from affecting others:

| Scenario | Impact With Monolith | Impact With Services |
|----------|---------------------|---------------------|
| AI Provider slow | Entire system slows | Only AI requests affected; others continue |
| Knowledge query spike | All requests delayed | Only knowledge lookups affected |
| Analytics backlog | Processing blocked | Core conversation unaffected |

#### Resource Optimization

Different services have different resource profiles:

| Service | Resource Profile | Optimization |
|---------|------------------|--------------|
| AI Provider Service | API-bound | Connection pooling; rate management |
| Knowledge Service | Memory-intensive | Read replicas; caching |
| Context Service | Low-latency storage | In-memory storage; fast access |
| Analytics Service | Throughput-focused | Batch processing; eventual consistency |

### 5.2 Autonomy Benefits

#### Agent Autonomy Preserved

The service decomposition directly supports the multi-agent autonomy model:

| Agent | Service | Autonomy Enabled |
|-------|---------|------------------|
| Primary Agent | Primary Agent Service | Independent decision-making within domain |
| Supervisor | Supervisor Service | Parallel monitoring without blocking |
| Escalation | Escalation Service | Specialized handoff capability |

#### Domain Autonomy

Each service owns its domain completely:

| Domain | Autonomy Benefit |
|--------|------------------|
| Session Management | Session decisions don't require AI involvement |
| Knowledge | Content updates don't require conversation restart |
| Customer Profile | Profile changes isolated from conversation logic |
| Analytics | Metrics processing independent of real-time flow |

#### Failure Autonomy

Services can fail independently without system-wide impact:

| Service Failure | System Behavior |
|-----------------|-----------------|
| Analytics Service | Conversations continue; metrics deferred |
| Knowledge Service | AI acknowledges gap; escalates if critical |
| Supervisor Service | AI continues; quality monitoring paused |
| Single AI Provider | Fallback to alternative; degraded but functional |

### 5.3 Alignment with Architecture

This service decomposition maps directly to the architectural layers:

| Architecture Layer | Services |
|-------------------|----------|
| Interaction Layer | Channel Gateway, Conversation |
| Routing Layer | Session, Routing |
| AI Agent Layer | Primary Agent, Supervisor, Escalation |
| Memory & Context Layer | Knowledge, Customer Profile, Context |
| Analytics Layer | Analytics, Audit |
| Integration Layer | Enterprise Gateway, AI Provider |

### 5.4 Alignment with Agent Model

The decomposition supports the agent interaction model:

| Agent Model Requirement | Service Support |
|------------------------|-----------------|
| Primary Agent autonomy | Dedicated service with full domain control |
| Supervisor parallel monitoring | Async communication; non-blocking |
| Escalation with context | Escalation Service compiles from Context Service |
| Confidence-based decisions | Primary Agent Service owns decision logic |
| Guardrail enforcement | Conversation Service applies before delivery |

---

## 6. Service Ownership

### 6.1 Service Ownership Matrix

| Service | Owning Team | Dependencies |
|---------|-------------|--------------|
| Channel Gateway | Platform | — |
| Conversation | Platform | Session, Primary Agent |
| Session | Platform | — |
| Routing | Platform | Session |
| Primary Agent | AI | Knowledge, Context, Profile, AI Provider, Enterprise GW |
| Supervisor | AI | Primary Agent (events) |
| Escalation | AI | Context, Routing |
| Knowledge | Data | — |
| Customer Profile | Data | — |
| Context | Data | — |
| Analytics | Operations | All (receives events) |
| Audit | Operations | All (receives events) |
| Enterprise Gateway | Integration | — |
| AI Provider | Integration | — |

### 6.2 Dependency Direction

Services depend in one direction — from interaction toward data and integration:

```
┌─────────────────────────────────────────────────────────────────┐
│                 DEPENDENCY DIRECTION                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  INTERACTION ───► SESSION ───► AI AGENT ───► DATA & INTEGRATION │
│                                                                  │
│  • Channel Gateway    • Session       • Primary Agent           │
│  • Conversation       • Routing       • Supervisor              │
│                                       • Escalation              │
│                                              │                   │
│                                              ▼                   │
│                                       • Knowledge               │
│                                       • Profile                 │
│                                       • Context                 │
│                                       • Enterprise GW           │
│                                       • AI Provider             │
│                                                                  │
│  OPERATIONS (receives from all, depended on by none)            │
│  • Analytics                                                     │
│  • Audit                                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Summary

### 7.1 Service Count by Domain

| Domain | Services | Purpose |
|--------|----------|---------|
| Customer Interaction | 2 | Handle customer communication |
| Session Management | 2 | Manage session lifecycle and routing |
| AI Agent | 3 | Execute AI-powered conversation handling |
| Knowledge & Data | 3 | Manage information and context |
| Operations | 2 | Observe and audit system behavior |
| Integration | 2 | Connect to external systems |
| **Total** | **14** | — |

### 7.2 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Separate Primary Agent and Supervisor | Enables parallel monitoring without blocking |
| Separate Knowledge and Context | Different lifecycles and scaling patterns |
| Dedicated Escalation Service | Specialized handoff logic isolated |
| AI Provider abstraction | Swap AI providers without core changes |
| Async analytics and audit | Don't slow down customer experience |

### 7.3 What This Enables

| Capability | How Decomposition Enables |
|------------|--------------------------|
| **Horizontal Scaling** | Scale each service independently |
| **Fault Isolation** | One service failure doesn't cascade |
| **Independent Deployment** | Update services without full system deployment |
| **Team Autonomy** | Teams own services end-to-end |
| **Technology Flexibility** | Services can use different technologies internally |

---

## Appendix A: Service Quick Reference

| Service | Does | Doesn't Do |
|---------|------|------------|
| Channel Gateway | Accept connections; stream audio/messages | Understand content; route; authenticate |
| Conversation | Orchestrate turns; apply guardrails | Generate responses; store context |
| Session | Manage session state; authentication context | Route; handle conversation; store profile |
| Routing | Assign agents; balance load; queue | Create sessions; execute conversations |
| Primary Agent | Understand; respond; decide; execute | Manage channels; store data; execute handoff |
| Supervisor | Monitor quality; advise; override | Interact with customer; generate responses |
| Escalation | Compile context; coordinate handoff | Decide to escalate; continue conversation |
| Knowledge | Retrieve information; search | Generate responses; store customer data |
| Customer Profile | Store/retrieve profile; history | Authenticate; generate responses |
| Context | Store/retrieve conversation context | Persist long-term; generate responses |
| Analytics | Collect metrics; aggregate; alert | Take action; store audit records |
| Audit | Create immutable records; support review | Real-time alerting; take action |
| Enterprise Gateway | Translate protocols; connect enterprise | Business logic; AI processing |
| AI Provider | Invoke AI models; manage rates | Prompt construction; decision logic |

---

## Appendix B: Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-17 | Backend Architecture | Initial service boundaries |

---

*This service decomposition provides the foundation for scalable, autonomous, and maintainable backend implementation. Each service has clear ownership and boundaries, enabling independent development and operation.*

# Event Flow Architecture

## AI-Powered Digital Call Center Using Autonomous AI Agents

**Document Version:** 1.0  
**Date:** January 17, 2026  
**Phase:** 4 — API & Backend Design  
**Alignment:** Service Boundaries, Agent Interaction Flow, Confidence Control System  

---

## 1. Event-Driven Design Philosophy

### 1.1 Why Events

The system uses events to achieve:

| Goal | How Events Help |
|------|-----------------|
| **Decoupling** | Services communicate without direct dependencies |
| **Autonomy** | Agents operate independently, coordinating through events |
| **Scalability** | Event consumers scale independently of producers |
| **Resilience** | Failures isolated; events can be replayed |
| **Observability** | Events provide natural audit and analytics trail |

### 1.2 Event vs. API Communication

| Aspect | API (Request-Response) | Event (Publish-Subscribe) |
|--------|------------------------|---------------------------|
| **Coupling** | Caller knows callee | Producer doesn't know consumers |
| **Timing** | Synchronous; caller waits | Asynchronous; fire and continue |
| **Failure Impact** | Caller fails if callee fails | Producer continues; consumers handle independently |
| **Use Case** | Need immediate answer | Notification; async processing |

### 1.3 Hybrid Model

The system uses both:

- **APIs** for synchronous operations where response is needed immediately
- **Events** for notifications, monitoring, logging, and decoupled coordination

---

## 2. Event Categories

### 2.1 Category Overview

| Category | Purpose | Timing | Criticality |
|----------|---------|--------|-------------|
| **Lifecycle Events** | Session start, end, state changes | Synchronous with action | High |
| **Conversation Events** | Turn exchanges, responses | Real-time | High |
| **Decision Events** | AI decisions with reasoning | Real-time | Medium |
| **Supervision Events** | Quality monitoring signals | Real-time | Medium |
| **Escalation Events** | Human handoff coordination | Real-time | High |
| **Analytics Events** | Metrics and measurements | Near real-time | Low |
| **Audit Events** | Compliance and investigation | Synchronous with action | High |
| **System Events** | Health, errors, capacity | Real-time | Variable |

---

## 3. Key Events

### 3.1 Lifecycle Events

#### SESSION_STARTED

Emitted when a new customer session is created.

| Attribute | Description |
|-----------|-------------|
| **Emitted By** | Session Service |
| **Timing** | After session successfully created |
| **Payload** | Session ID, channel, customer identifier, agent assigned, timestamp |

| Consumer | Purpose |
|----------|---------|
| Analytics Service | Track session count, channel distribution |
| Supervisor Service | Begin monitoring this session |
| Audit Service | Log session initiation |

---

#### SESSION_ENDED

Emitted when a session terminates.

| Attribute | Description |
|-----------|-------------|
| **Emitted By** | Session Service |
| **Timing** | After session successfully closed |
| **Payload** | Session ID, duration, turn count, resolution status, termination reason |

| Consumer | Purpose |
|----------|---------|
| Analytics Service | Track resolution rate, handle time |
| Context Service | Archive or cleanup context |
| Audit Service | Log session completion |

---

#### SESSION_STATE_CHANGED

Emitted when session state transitions.

| Attribute | Description |
|-----------|-------------|
| **Emitted By** | Session Service |
| **Timing** | On state transition |
| **Payload** | Session ID, previous state, new state, trigger reason |

| Consumer | Purpose |
|----------|---------|
| Analytics Service | Track state distribution |
| Supervisor Service | Monitor for unexpected transitions |

---

### 3.2 Conversation Events

#### CUSTOMER_MESSAGE_RECEIVED

Emitted when customer input is received and processed.

| Attribute | Description |
|-----------|-------------|
| **Emitted By** | Conversation Service |
| **Timing** | After input received and transcribed |
| **Payload** | Session ID, turn number, message content, channel, transcription confidence |

| Consumer | Purpose |
|----------|---------|
| Supervisor Service | Monitor conversation quality |
| Analytics Service | Track message volume, transcription quality |
| Audit Service | Log customer input |

---

#### AGENT_RESPONSE_DELIVERED

Emitted when AI agent response is delivered to customer.

| Attribute | Description |
|-----------|-------------|
| **Emitted By** | Conversation Service |
| **Timing** | After response delivered |
| **Payload** | Session ID, turn number, response content, response latency |

| Consumer | Purpose |
|----------|---------|
| Supervisor Service | Review response quality |
| Analytics Service | Track response latency, turn patterns |
| Audit Service | Log agent response |

---

#### CONVERSATION_TURN_COMPLETED

Emitted when a full turn (customer input + agent response) is complete.

| Attribute | Description |
|-----------|-------------|
| **Emitted By** | Conversation Service |
| **Timing** | After turn fully processed |
| **Payload** | Session ID, turn number, intent, emotion, confidence, action taken |

| Consumer | Purpose |
|----------|---------|
| Supervisor Service | Evaluate turn quality |
| Context Service | Confirm context update |
| Analytics Service | Track conversation metrics |

---

### 3.3 Decision Events

#### INTENT_DETECTED

Emitted when Primary Agent determines customer intent.

| Attribute | Description |
|-----------|-------------|
| **Emitted By** | Primary Agent Service |
| **Timing** | During turn processing |
| **Payload** | Session ID, turn number, detected intent, confidence level, supporting signals |

| Consumer | Purpose |
|----------|---------|
| Supervisor Service | Monitor detection accuracy |
| Analytics Service | Track intent distribution |
| Audit Service | Log intent decision |

---

#### CONFIDENCE_ASSESSED

Emitted when Primary Agent assesses its confidence.

| Attribute | Description |
|-----------|-------------|
| **Emitted By** | Primary Agent Service |
| **Timing** | During turn processing |
| **Payload** | Session ID, turn number, confidence dimensions (understanding, knowledge, authority, outcome), overall confidence |

| Consumer | Purpose |
|----------|---------|
| Supervisor Service | Watch for low confidence patterns |
| Analytics Service | Track confidence distribution |

---

#### EMOTION_DETECTED

Emitted when customer emotional state is assessed.

| Attribute | Description |
|-----------|-------------|
| **Emitted By** | Primary Agent Service |
| **Timing** | During turn processing |
| **Payload** | Session ID, turn number, detected emotion, previous emotion, confidence, change trigger |

| Consumer | Purpose |
|----------|---------|
| Supervisor Service | Monitor for escalating emotion |
| Analytics Service | Track sentiment trends |
| Audit Service | Log emotion assessment |

---

#### ACTION_DECIDED

Emitted when Primary Agent decides on an action.

| Attribute | Description |
|-----------|-------------|
| **Emitted By** | Primary Agent Service |
| **Timing** | Before action execution |
| **Payload** | Session ID, turn number, action type, action details, confidence, reasoning summary |

| Consumer | Purpose |
|----------|---------|
| Supervisor Service | Verify action appropriateness |
| Audit Service | Log action decision with reasoning |

---

#### ACTION_EXECUTED

Emitted when an action is completed.

| Attribute | Description |
|-----------|-------------|
| **Emitted By** | Primary Agent Service |
| **Timing** | After action completion |
| **Payload** | Session ID, turn number, action type, success/failure, result summary |

| Consumer | Purpose |
|----------|---------|
| Supervisor Service | Confirm action success |
| Analytics Service | Track action success rates |
| Audit Service | Log action outcome |

---

### 3.4 Supervision Events

#### SUPERVISION_ADVISORY_ISSUED

Emitted when Supervisor Agent sends guidance to Primary Agent.

| Attribute | Description |
|-----------|-------------|
| **Emitted By** | Supervisor Service |
| **Timing** | When intervention warranted |
| **Payload** | Session ID, advisory type, message, priority, action required |

| Consumer | Purpose |
|----------|---------|
| Primary Agent Service | Incorporate guidance |
| Analytics Service | Track supervision frequency |
| Audit Service | Log supervisor intervention |

---

#### SUPERVISION_CONCERN_RAISED

Emitted when Supervisor detects a quality or policy concern.

| Attribute | Description |
|-----------|-------------|
| **Emitted By** | Supervisor Service |
| **Timing** | When concern identified |
| **Payload** | Session ID, concern type, severity, evidence, recommended action |

| Consumer | Purpose |
|----------|---------|
| Escalation Service | Evaluate for escalation |
| Analytics Service | Track quality issues |
| Audit Service | Log concern |

---

#### GUARDRAIL_TRIGGERED

Emitted when a guardrail check blocks or modifies output.

| Attribute | Description |
|-----------|-------------|
| **Emitted By** | Conversation Service (Guardrail component) |
| **Timing** | During response validation |
| **Payload** | Session ID, turn number, guardrail type, trigger reason, action taken |

| Consumer | Purpose |
|----------|---------|
| Supervisor Service | Review guardrail patterns |
| Analytics Service | Track guardrail activations |
| Audit Service | Log guardrail enforcement |

---

### 3.5 Escalation Events

#### ESCALATION_TRIGGERED

Emitted when escalation to human is initiated.

| Attribute | Description |
|-----------|-------------|
| **Emitted By** | Primary Agent Service or Supervisor Service |
| **Timing** | When escalation decision made |
| **Payload** | Session ID, trigger source, escalation type, reason code, reason detail, priority |

| Consumer | Purpose |
|----------|---------|
| Escalation Service | Begin escalation workflow |
| Routing Service | Prepare for human assignment |
| Analytics Service | Track escalation rate |
| Audit Service | Log escalation trigger |

---

#### ESCALATION_CONTEXT_PREPARED

Emitted when context package for human agent is ready.

| Attribute | Description |
|-----------|-------------|
| **Emitted By** | Escalation Service |
| **Timing** | After context compilation |
| **Payload** | Session ID, escalation ID, context package ID, summary, key points |

| Consumer | Purpose |
|----------|---------|
| Routing Service | Proceed with assignment |
| Audit Service | Log context package |

---

#### HUMAN_AGENT_ASSIGNED

Emitted when a human agent is assigned to handle escalation.

| Attribute | Description |
|-----------|-------------|
| **Emitted By** | Routing Service |
| **Timing** | When human agent assigned |
| **Payload** | Session ID, escalation ID, human agent ID, queue wait time |

| Consumer | Purpose |
|----------|---------|
| Escalation Service | Complete handoff |
| Session Service | Update session state |
| Analytics Service | Track assignment metrics |

---

#### ESCALATION_COMPLETED

Emitted when handoff to human is complete.

| Attribute | Description |
|-----------|-------------|
| **Emitted By** | Escalation Service |
| **Timing** | After handoff confirmed |
| **Payload** | Session ID, escalation ID, handoff duration, success status |

| Consumer | Purpose |
|----------|---------|
| Session Service | Transition session to human-handled |
| Analytics Service | Track escalation success |
| Audit Service | Log escalation completion |

---

### 3.6 System Events

#### SERVICE_HEALTH_CHANGED

Emitted when a service's health status changes.

| Attribute | Description |
|-----------|-------------|
| **Emitted By** | Any Service |
| **Timing** | On health state change |
| **Payload** | Service ID, previous status, new status, reason |

| Consumer | Purpose |
|----------|---------|
| Analytics Service | Track system health |
| Routing Service | Adjust routing if capacity affected |

---

#### ERROR_OCCURRED

Emitted when a significant error occurs.

| Attribute | Description |
|-----------|-------------|
| **Emitted By** | Any Service |
| **Timing** | When error detected |
| **Payload** | Service ID, session ID (if applicable), error category, error detail, severity |

| Consumer | Purpose |
|----------|---------|
| Analytics Service | Track error rates |
| Audit Service | Log error for investigation |

---

#### CAPACITY_THRESHOLD_CROSSED

Emitted when capacity limits are approached or exceeded.

| Attribute | Description |
|-----------|-------------|
| **Emitted By** | Routing Service |
| **Timing** | When threshold crossed |
| **Payload** | Resource type, current level, threshold, direction (approaching/exceeded) |

| Consumer | Purpose |
|----------|---------|
| Analytics Service | Track capacity trends |

---

## 4. Event Flow Diagrams

### 4.1 Standard Conversation Turn

```
┌─────────────────────────────────────────────────────────────────┐
│              EVENT FLOW: CONVERSATION TURN                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Customer speaks                                                 │
│       │                                                          │
│       ▼                                                          │
│  CUSTOMER_MESSAGE_RECEIVED ─────────► Supervisor Service        │
│       │                      ─────────► Analytics Service        │
│       │                      ─────────► Audit Service            │
│       ▼                                                          │
│  Primary Agent processes                                         │
│       │                                                          │
│       ├──► INTENT_DETECTED ─────────► Supervisor, Analytics     │
│       │                                                          │
│       ├──► CONFIDENCE_ASSESSED ─────► Supervisor, Analytics     │
│       │                                                          │
│       ├──► EMOTION_DETECTED ────────► Supervisor, Analytics     │
│       │                                                          │
│       ├──► ACTION_DECIDED ──────────► Supervisor, Audit         │
│       │                                                          │
│       ▼                                                          │
│  AGENT_RESPONSE_DELIVERED ──────────► Supervisor, Analytics     │
│       │                      ─────────► Audit Service            │
│       ▼                                                          │
│  CONVERSATION_TURN_COMPLETED ───────► All interested services   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Confidence-Based Escalation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│         EVENT FLOW: CONFIDENCE-BASED ESCALATION                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Primary Agent detects low confidence                            │
│       │                                                          │
│       ▼                                                          │
│  CONFIDENCE_ASSESSED (level: low)                                │
│       │                                                          │
│       └────────────────────────► Supervisor Service              │
│                                       │                          │
│                                       ▼                          │
│                             Supervisor evaluates                 │
│                                       │                          │
│                              ┌────────┴────────┐                │
│                              │                 │                │
│                         Continue          Intervene              │
│                              │                 │                │
│                              ▼                 ▼                │
│                    (No event)     SUPERVISION_ADVISORY_ISSUED   │
│                                        │                        │
│                                        ▼                        │
│                               Primary Agent receives            │
│                                        │                        │
│                                ┌───────┴───────┐               │
│                                │               │               │
│                           Recovers      Still struggling        │
│                                │               │               │
│                                ▼               ▼               │
│                         (Continue)    ESCALATION_TRIGGERED      │
│                                              │                  │
│                                              ▼                  │
│                                     Escalation Service          │
│                                              │                  │
│                                              ▼                  │
│                              ESCALATION_CONTEXT_PREPARED        │
│                                              │                  │
│                                              ▼                  │
│                                     Routing Service             │
│                                              │                  │
│                                              ▼                  │
│                                HUMAN_AGENT_ASSIGNED             │
│                                              │                  │
│                                              ▼                  │
│                                ESCALATION_COMPLETED             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Supervisor Monitoring Flow

```
┌─────────────────────────────────────────────────────────────────┐
│            EVENT FLOW: SUPERVISOR MONITORING                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Supervisor Service receives events continuously:                │
│                                                                  │
│  INTENT_DETECTED                                                 │
│  CONFIDENCE_ASSESSED      ─────────► Supervisor evaluates       │
│  EMOTION_DETECTED                    in parallel                │
│  ACTION_DECIDED                           │                     │
│  AGENT_RESPONSE_DELIVERED                 │                     │
│                                           ▼                     │
│                                   ┌───────────────┐             │
│                                   │   Analysis    │             │
│                                   └───────┬───────┘             │
│                                           │                     │
│          ┌────────────────────────────────┼─────────────────┐   │
│          │                                │                 │   │
│          ▼                                ▼                 ▼   │
│    No concern                     Minor concern       Major concern  │
│          │                                │                 │   │
│          ▼                                ▼                 ▼   │
│    (No event)              SUPERVISION_ADVISORY    SUPERVISION_CONCERN │
│                                     │                       │   │
│                                     ▼                       ▼   │
│                            Primary Agent          Escalation triggered │
│                            adjusts                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. How Events Decouple Agents from APIs

### 5.1 Decoupling Mechanism

Events allow agents to communicate without direct API calls:

```
┌─────────────────────────────────────────────────────────────────┐
│                    DECOUPLING THROUGH EVENTS                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  WITHOUT EVENTS (Tight Coupling):                                │
│                                                                  │
│  Primary Agent ─────► API Call ─────► Supervisor Service        │
│       │                                      │                  │
│       └─────────── Waits ───────────────────┘                   │
│                                                                  │
│  • Primary Agent must know Supervisor API                        │
│  • Primary Agent blocked while Supervisor processes              │
│  • If Supervisor fails, Primary Agent fails                      │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  WITH EVENTS (Loose Coupling):                                   │
│                                                                  │
│  Primary Agent ─────► Emit Event ─────► Event Channel           │
│       │                                      │                  │
│       └─────── Continues ───────┐            │                  │
│                                 │            ▼                  │
│                                 │    Supervisor receives        │
│                                 │    (asynchronously)           │
│                                 │            │                  │
│                                 │            ▼                  │
│                                 │    Processes independently    │
│                                 │            │                  │
│                                 │            ▼                  │
│                                 │    May emit advisory event    │
│                                 │            │                  │
│                                 ▼            ▼                  │
│                           Primary Agent receives                │
│                           (when available)                      │
│                                                                  │
│  • Primary Agent doesn't know who consumes events               │
│  • Primary Agent continues without waiting                      │
│  • Supervisor failure doesn't block Primary Agent               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Benefits for Agent Autonomy

| Aspect | How Events Enable |
|--------|-------------------|
| **Primary Agent Independence** | Emits events; doesn't wait for Supervisor response |
| **Supervisor Parallel Operation** | Consumes events asynchronously; doesn't block conversation |
| **Escalation Decoupling** | Triggers escalation via event; doesn't manage handoff directly |
| **New Consumer Addition** | Add new consumers without changing producers |
| **Failure Isolation** | Consumer failure doesn't affect producer |

### 5.3 Event vs. API by Interaction

| Interaction | Communication | Reason |
|-------------|---------------|--------|
| Primary Agent → Knowledge Service | API | Needs answer to respond to customer |
| Primary Agent → Supervisor | Event | Notification only; doesn't need response |
| Supervisor → Primary Agent | Event | Advisory only; Primary decides to incorporate |
| Primary Agent → Escalation | Event | Initiates async workflow |
| Escalation → Routing | API | Needs human assignment to proceed |
| Any Service → Analytics | Event | Fire-and-forget metrics |
| Any Service → Audit | Event | Fire-and-forget logging |

---

## 6. Failure Propagation

### 6.1 Failure Isolation Principle

Events enable failures to be contained:

| Failure Type | Impact with Events |
|--------------|-------------------|
| Consumer failure | Producer continues; events queued |
| Producer failure | Other producers/consumers unaffected |
| Event delivery failure | Retry and dead-letter handling |
| Slow consumer | Producer not slowed; backpressure managed |

### 6.2 Failure Scenarios

#### Scenario: Analytics Service Fails

```
┌─────────────────────────────────────────────────────────────────┐
│           FAILURE: ANALYTICS SERVICE DOWN                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Primary Agent ─────► CONVERSATION_TURN_COMPLETED                │
│       │                         │                               │
│       │                         ├───────► Supervisor ✓          │
│       │                         │                               │
│       │                         ├───────► Analytics ✗           │
│       │                         │              │                │
│       │                         │         Event queued          │
│       │                         │              │                │
│       │                         └───────► Audit ✓               │
│       │                                                          │
│       ▼                                                          │
│  Continues serving customer (unaffected)                        │
│                                                                  │
│  Later: Analytics recovers ─────► Processes queued events       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Scenario: Supervisor Service Fails

```
┌─────────────────────────────────────────────────────────────────┐
│           FAILURE: SUPERVISOR SERVICE DOWN                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Primary Agent ─────► Decision events                            │
│       │                    │                                    │
│       │                    └───────► Supervisor ✗               │
│       │                                   │                     │
│       │                              Events queued              │
│       │                                                          │
│       ▼                                                          │
│  Continues serving customer                                      │
│  (operates autonomously without supervision)                    │
│                                                                  │
│  MITIGATION:                                                     │
│  • Primary Agent has full decision authority within bounds      │
│  • Guardrails still enforced (different service)               │
│  • Audit still logging (different service)                     │
│  • When Supervisor recovers, can review queued events          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Scenario: Audit Service Fails

```
┌─────────────────────────────────────────────────────────────────┐
│             FAILURE: AUDIT SERVICE DOWN                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CRITICAL: Audit is compliance-required                         │
│                                                                  │
│  Options based on severity:                                      │
│                                                                  │
│  OPTION A: Continue with local buffering                        │
│  • Events buffered locally                                      │
│  • Flushed when Audit recovers                                  │
│  • Suitable for brief outages                                   │
│                                                                  │
│  OPTION B: Degrade to synchronous logging                       │
│  • Write audit synchronously to backup                          │
│  • Slower but ensures compliance                                │
│  • Suitable for extended outages                                │
│                                                                  │
│  OPTION C: Stop accepting new sessions                          │
│  • Existing sessions continue                                   │
│  • New sessions get "temporary unavailable"                     │
│  • Suitable for critical compliance requirements               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 Event Delivery Guarantees

| Guarantee Level | Behavior | Used For |
|-----------------|----------|----------|
| **At-least-once** | Retry until acknowledged; may duplicate | Most events |
| **At-most-once** | No retry; may lose | Non-critical metrics |
| **Exactly-once** | Deduplication at consumer | Critical audit events |

### 6.4 Dead Letter Handling

Events that cannot be processed after retries:

```
┌─────────────────────────────────────────────────────────────────┐
│                 DEAD LETTER FLOW                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Event ─────► Consumer (fails)                                   │
│                    │                                             │
│                    ▼                                             │
│              Retry (N times)                                     │
│                    │                                             │
│                    ▼                                             │
│              Still failing                                       │
│                    │                                             │
│                    ▼                                             │
│              Move to Dead Letter Queue                           │
│                    │                                             │
│                    ▼                                             │
│              Alert Operations                                    │
│                    │                                             │
│                    ▼                                             │
│              Manual investigation                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Analytics and Audit Triggering

### 7.1 Analytics Event Flow

Analytics receives events from all services and aggregates metrics:

```
┌─────────────────────────────────────────────────────────────────┐
│                 ANALYTICS EVENT FLOW                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐                                            │
│  │ Session Service │──► SESSION_STARTED                         │
│  │                 │──► SESSION_ENDED                           │
│  └─────────────────┘         │                                  │
│                              │                                  │
│  ┌─────────────────┐         │                                  │
│  │ Conversation    │──► CUSTOMER_MESSAGE_RECEIVED               │
│  │ Service         │──► AGENT_RESPONSE_DELIVERED     ─────────► │
│  └─────────────────┘         │                       │          │
│                              │                       │          │
│  ┌─────────────────┐         │                       ▼          │
│  │ Primary Agent   │──► INTENT_DETECTED      ┌────────────────┐ │
│  │ Service         │──► CONFIDENCE_ASSESSED  │   Analytics    │ │
│  │                 │──► EMOTION_DETECTED     │    Service     │ │
│  │                 │──► ACTION_EXECUTED      │                │ │
│  └─────────────────┘         │               │  • Aggregates  │ │
│                              │               │  • Calculates  │ │
│  ┌─────────────────┐         │               │  • Stores      │ │
│  │ Supervisor      │──► SUPERVISION_ADVISORY │  • Alerts      │ │
│  │ Service         │──► GUARDRAIL_TRIGGERED  │                │ │
│  └─────────────────┘         │               └────────────────┘ │
│                              │                       │          │
│  ┌─────────────────┐         │                       │          │
│  │ Escalation      │──► ESCALATION_TRIGGERED         │          │
│  │ Service         │──► ESCALATION_COMPLETED         │          │
│  └─────────────────┘         │                       │          │
│                              │                       ▼          │
│                              └──────────────► Dashboards        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Metrics Derived from Events

| Metric | Source Events |
|--------|---------------|
| Active sessions | SESSION_STARTED, SESSION_ENDED |
| Resolution rate | SESSION_ENDED (resolution_status) |
| Average handle time | SESSION_STARTED, SESSION_ENDED (duration) |
| Escalation rate | ESCALATION_TRIGGERED, SESSION_ENDED |
| Intent distribution | INTENT_DETECTED |
| Sentiment trend | EMOTION_DETECTED |
| Confidence levels | CONFIDENCE_ASSESSED |
| Guardrail activations | GUARDRAIL_TRIGGERED |
| Response latency | AGENT_RESPONSE_DELIVERED |
| Supervisor interventions | SUPERVISION_ADVISORY_ISSUED |

### 7.3 Audit Event Flow

Audit receives compliance-critical events and creates immutable records:

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUDIT EVENT FLOW                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  AUDIT-REQUIRED EVENTS:                                          │
│                                                                  │
│  SESSION_STARTED              ───────────────────────┐          │
│  SESSION_ENDED                                       │          │
│  CUSTOMER_MESSAGE_RECEIVED                           │          │
│  AGENT_RESPONSE_DELIVERED                            ▼          │
│  INTENT_DETECTED                            ┌────────────────┐  │
│  EMOTION_DETECTED                           │     Audit      │  │
│  ACTION_DECIDED ◄─── (includes reasoning)   │    Service     │  │
│  ACTION_EXECUTED                            │                │  │
│  GUARDRAIL_TRIGGERED                        │  • Validates   │  │
│  ESCALATION_TRIGGERED                       │  • Stores      │  │
│  ESCALATION_COMPLETED                       │  • Indexes     │  │
│  SUPERVISION_ADVISORY_ISSUED                │  • Immutable   │  │
│  SUPERVISION_CONCERN_RAISED                 │                │  │
│  ERROR_OCCURRED                             └────────────────┘  │
│                                                      │          │
│                                                      ▼          │
│                                              ┌────────────────┐ │
│                                              │  Audit Store   │ │
│                                              │  (Immutable)   │ │
│                                              └────────────────┘ │
│                                                      │          │
│                                                      ▼          │
│                                              Investigation &    │
│                                              Compliance Queries │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.4 Audit Record Requirements

| Requirement | Implementation |
|-------------|----------------|
| **Immutability** | Records cannot be modified after creation |
| **Completeness** | All decision-related events captured |
| **Traceability** | Events linked by session and correlation IDs |
| **Explainability** | ACTION_DECIDED includes reasoning |
| **Timeliness** | Events written synchronously or with guaranteed delivery |
| **Retention** | Records retained per compliance policy |

---

## 8. Event Schema Conventions

### 8.1 Common Event Structure

All events follow a common structure:

```json
{
  "event_id": "unique-event-identifier",
  "event_type": "EVENT_TYPE_NAME",
  "timestamp": "ISO-8601 timestamp",
  "correlation_id": "session-or-trace-id",
  "source": {
    "service": "emitting-service-name",
    "instance": "instance-identifier"
  },
  "payload": {
    // Event-specific data
  },
  "metadata": {
    "version": "1.0",
    "environment": "production | staging | demo"
  }
}
```

### 8.2 Event Naming Convention

| Pattern | Example | Description |
|---------|---------|-------------|
| NOUN_VERB_PAST | SESSION_STARTED | Something happened |
| NOUN_VERB_PAST | INTENT_DETECTED | Detection completed |
| NOUN_NOUN_VERB_PAST | SUPERVISION_ADVISORY_ISSUED | Compound action |

---

## 9. Summary

### 9.1 Event Count by Category

| Category | Event Count | Primary Consumers |
|----------|-------------|-------------------|
| Lifecycle | 3 | Analytics, Audit, Supervisor |
| Conversation | 3 | Analytics, Audit, Supervisor |
| Decision | 5 | Supervisor, Analytics, Audit |
| Supervision | 3 | Primary Agent, Analytics, Audit |
| Escalation | 4 | Routing, Session, Analytics, Audit |
| System | 3 | Analytics |
| **Total** | **21** | — |

### 9.2 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Supervisor consumes events, not API | Non-blocking monitoring |
| Decision events include reasoning | Explainability and audit |
| Analytics is event-only | No impact on conversation latency |
| Audit has delivery guarantee | Compliance requirement |
| Failure doesn't block producers | Resilience and autonomy |

### 9.3 Alignment Summary

| Design Element | Event Flow Alignment |
|----------------|---------------------|
| **Confidence Control** | CONFIDENCE_ASSESSED triggers supervision and escalation |
| **Supervisor Parallel Operation** | Event-based; doesn't block Primary Agent |
| **Escalation Triggers** | ESCALATION_TRIGGERED initiates async workflow |
| **Guardrail Enforcement** | GUARDRAIL_TRIGGERED logged for review |
| **Audit Requirements** | All decisions logged with reasoning |

---

## Appendix A: Event Quick Reference

| Event | Emitter | Key Consumers |
|-------|---------|---------------|
| SESSION_STARTED | Session | Analytics, Supervisor, Audit |
| SESSION_ENDED | Session | Analytics, Context, Audit |
| CUSTOMER_MESSAGE_RECEIVED | Conversation | Supervisor, Analytics, Audit |
| AGENT_RESPONSE_DELIVERED | Conversation | Supervisor, Analytics, Audit |
| INTENT_DETECTED | Primary Agent | Supervisor, Analytics, Audit |
| CONFIDENCE_ASSESSED | Primary Agent | Supervisor, Analytics |
| EMOTION_DETECTED | Primary Agent | Supervisor, Analytics, Audit |
| ACTION_DECIDED | Primary Agent | Supervisor, Audit |
| ACTION_EXECUTED | Primary Agent | Supervisor, Analytics, Audit |
| SUPERVISION_ADVISORY_ISSUED | Supervisor | Primary Agent, Analytics, Audit |
| GUARDRAIL_TRIGGERED | Conversation | Supervisor, Analytics, Audit |
| ESCALATION_TRIGGERED | Primary Agent / Supervisor | Escalation, Analytics, Audit |
| ESCALATION_COMPLETED | Escalation | Session, Analytics, Audit |

---

## Appendix B: Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-17 | Event Architecture | Initial event flow specification |

---

*Events enable the autonomous agent system to operate with loose coupling, parallel supervision, and resilient failure handling. The event-driven model supports the confidence-based control system by allowing supervision to occur without blocking conversation flow.*

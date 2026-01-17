# Backend Codebase Blueprint

## AI-Powered Digital Call Center Using Autonomous AI Agents

**Document Version:** 1.0  
**Date:** January 17, 2026  
**Phase:** 4 — API & Backend Design  
**Purpose:** Codebase Organization Guide  

---

## 1. Design Principles

### 1.1 Organization Goals

| Goal | How Structure Achieves It |
|------|---------------------------|
| **Separation of Concerns** | Each module has single responsibility |
| **Agent Isolation** | Agent logic independent of transport layer |
| **Testability** | Core logic testable without infrastructure |
| **Scalability** | Services deployable independently |
| **Maintainability** | Clear boundaries reduce cognitive load |

### 1.2 Layered Architecture

The codebase follows a layered structure where dependencies flow inward:

```
┌─────────────────────────────────────────────────────────────────┐
│                      DEPENDENCY DIRECTION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  OUTER LAYERS                              INNER LAYERS          │
│                                                                  │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐      │
│  │   API   │───►│ Service │───►│  Core   │───►│ Domain  │      │
│  │ (HTTP)  │    │ (Orch.) │    │ (Logic) │    │(Entities)│      │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘      │
│                                                                  │
│  Infrastructure dependencies point INWARD                       │
│  Domain has ZERO external dependencies                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Top-Level Folder Structure

```
backend/
├── api/                    # API layer (HTTP, WebSocket handlers)
├── services/               # Service orchestration layer
├── agents/                 # AI agent logic (autonomous)
├── core/                   # Core business logic
├── domain/                 # Domain entities and contracts
├── infrastructure/         # External integrations
├── events/                 # Event definitions and handlers
├── knowledge/              # Knowledge retrieval logic
├── context/                # Context management
├── analytics/              # Metrics and reporting
├── audit/                  # Audit logging
├── config/                 # Configuration management
├── common/                 # Shared utilities
└── tests/                  # Test suites
```

---

## 3. Module Specifications

### 3.1 API Module (`api/`)

#### Purpose
Handle all external communication protocols. Transform HTTP/WebSocket requests into internal service calls.

#### Structure
```
api/
├── http/                   # HTTP endpoint handlers
│   ├── session/            # Session management endpoints
│   ├── conversation/       # Message exchange endpoints
│   ├── escalation/         # Escalation endpoints
│   ├── analytics/          # Analytics query endpoints
│   └── health/             # Health check endpoints
├── websocket/              # WebSocket handlers
│   ├── voice/              # Voice streaming
│   └── chat/               # Chat messaging
├── middleware/             # Cross-cutting concerns
│   ├── authentication/     # Auth handling
│   ├── validation/         # Request validation
│   ├── error_handling/     # Error transformation
│   └── correlation/        # Request correlation
├── dto/                    # Data transfer objects
│   ├── requests/           # Incoming request shapes
│   └── responses/          # Outgoing response shapes
└── routes/                 # Route definitions
```

#### Responsibilities
- Parse incoming requests
- Validate request structure
- Transform DTOs to domain objects
- Call appropriate service layer
- Transform responses back to DTOs
- Handle HTTP/WebSocket protocol specifics

#### Does NOT Contain
- Business logic
- Agent decision-making
- Direct data access
- Event emission (delegates to services)

---

### 3.2 Services Module (`services/`)

#### Purpose
Orchestrate operations across multiple domains. Coordinate between agents, data, and external systems.

#### Structure
```
services/
├── session/                # Session management orchestration
│   ├── session_service     # Session lifecycle
│   └── routing_service     # Agent routing
├── conversation/           # Conversation orchestration
│   ├── conversation_service # Turn management
│   └── guardrail_service   # Response validation
├── escalation/             # Escalation orchestration
│   ├── escalation_service  # Handoff coordination
│   └── context_compiler    # Context package creation
├── profile/                # Customer profile orchestration
│   └── profile_service     # Profile access
└── supervisor/             # Supervision orchestration
    └── supervisor_service  # Quality monitoring
```

#### Responsibilities
- Coordinate multi-step operations
- Invoke agents for AI decisions
- Manage transactions
- Emit events for completed operations
- Handle service-level error recovery

#### Does NOT Contain
- AI reasoning logic (delegates to agents)
- HTTP handling
- Direct external API calls (delegates to infrastructure)

---

### 3.3 Agents Module (`agents/`)

#### Purpose
Contain all autonomous AI agent logic. This is where decisions are made.

#### Structure
```
agents/
├── primary/                # Primary Interaction Agent
│   ├── agent               # Main agent logic
│   ├── intent/             # Intent detection
│   │   ├── detector        # Intent classification
│   │   └── taxonomy        # Intent definitions
│   ├── emotion/            # Emotion assessment
│   │   ├── detector        # Emotion classification
│   │   └── taxonomy        # Emotion definitions
│   ├── confidence/         # Confidence scoring
│   │   ├── scorer          # Confidence calculation
│   │   └── thresholds      # Threshold definitions
│   ├── response/           # Response generation
│   │   ├── generator       # Response creation
│   │   └── templates       # Response patterns
│   └── workflow/           # Workflow execution
│       ├── executor        # Workflow runner
│       └── workflows/      # Defined workflows
├── supervisor/             # Supervisor Agent
│   ├── agent               # Supervisor logic
│   ├── monitors/           # Quality monitors
│   │   ├── confidence_monitor
│   │   ├── sentiment_monitor
│   │   └── policy_monitor
│   └── advisors/           # Advisory generators
│       ├── tone_advisor
│       └── escalation_advisor
├── escalation/             # Escalation Agent
│   ├── agent               # Escalation logic
│   ├── triggers/           # Escalation triggers
│   └── context_builder     # Context compilation
└── contracts/              # Agent interfaces
    ├── primary_agent       # Primary agent contract
    ├── supervisor_agent    # Supervisor agent contract
    └── escalation_agent    # Escalation agent contract
```

#### Responsibilities
- Make AI decisions (intent, emotion, confidence)
- Generate responses
- Execute business workflows
- Determine escalation needs
- Provide reasoning for decisions

#### Does NOT Contain
- HTTP handling
- Service orchestration
- Data persistence logic
- External API calls

---

### 3.4 Core Module (`core/`)

#### Purpose
Business logic that is not AI-specific. Rules, calculations, and operations.

#### Structure
```
core/
├── session/                # Session business logic
│   ├── session_manager     # Session state machine
│   └── session_validator   # Session rules
├── conversation/           # Conversation logic
│   ├── turn_manager        # Turn sequencing
│   └── transcript_builder  # Transcript construction
├── escalation/             # Escalation logic
│   ├── priority_calculator # Priority rules
│   └── skill_matcher       # Agent skill matching
├── guardrails/             # Guardrail rules
│   ├── content_safety      # Content filtering
│   ├── policy_compliance   # Policy rules
│   └── authority_bounds    # Authority limits
└── analytics/              # Analytics calculations
    ├── metrics_calculator  # Metric formulas
    └── aggregator          # Aggregation logic
```

#### Responsibilities
- Business rule evaluation
- State management logic
- Calculations and transformations
- Validation rules

#### Does NOT Contain
- AI agent logic
- Infrastructure concerns
- API handling

---

### 3.5 Domain Module (`domain/`)

#### Purpose
Define the core entities, value objects, and contracts. Zero dependencies.

#### Structure
```
domain/
├── entities/               # Domain entities
│   ├── session             # Session entity
│   ├── conversation        # Conversation entity
│   ├── turn                # Turn entity
│   ├── customer            # Customer entity
│   ├── decision            # Decision entity
│   └── escalation          # Escalation entity
├── value_objects/          # Value objects
│   ├── session_id          # Session identifier
│   ├── intent              # Intent classification
│   ├── emotion             # Emotion state
│   ├── confidence          # Confidence level
│   └── priority            # Priority level
├── contracts/              # Interfaces/contracts
│   ├── repositories/       # Data access contracts
│   │   ├── session_repository
│   │   ├── context_repository
│   │   └── profile_repository
│   ├── providers/          # External provider contracts
│   │   ├── ai_provider
│   │   ├── speech_provider
│   │   └── enterprise_provider
│   └── services/           # Service contracts
│       └── event_publisher
├── events/                 # Domain event definitions
│   ├── session_events
│   ├── conversation_events
│   └── decision_events
└── errors/                 # Domain-specific errors
    ├── session_errors
    ├── validation_errors
    └── escalation_errors
```

#### Responsibilities
- Define what data looks like
- Define contracts for data access
- Define domain events
- Define domain-specific errors

#### Does NOT Contain
- Implementation details
- External dependencies
- Business logic (only structure)

---

### 3.6 Infrastructure Module (`infrastructure/`)

#### Purpose
Implement all external integrations. Data storage, external APIs, messaging.

#### Structure
```
infrastructure/
├── persistence/            # Data storage
│   ├── session/            # Session storage
│   │   └── session_repository_impl
│   ├── context/            # Context storage
│   │   └── context_repository_impl
│   ├── profile/            # Profile storage
│   │   └── profile_repository_impl
│   └── audit/              # Audit storage
│       └── audit_repository_impl
├── providers/              # External API providers
│   ├── ai/                 # AI model providers
│   │   ├── ai_provider_impl
│   │   └── fallback_provider
│   ├── speech/             # Speech services
│   │   ├── stt_provider    # Speech-to-text
│   │   └── tts_provider    # Text-to-speech
│   └── enterprise/         # Enterprise systems
│       ├── crm_adapter
│       ├── order_adapter
│       └── scheduling_adapter
├── messaging/              # Event/message infrastructure
│   ├── event_publisher_impl
│   └── event_consumer
└── cache/                  # Caching infrastructure
    └── cache_provider
```

#### Responsibilities
- Implement repository contracts
- Implement provider contracts
- Handle connection management
- Handle serialization/deserialization
- Handle retries and circuit breaking

#### Does NOT Contain
- Business logic
- Agent logic
- API handling

---

### 3.7 Events Module (`events/`)

#### Purpose
Event publishing, consumption, and routing.

#### Structure
```
events/
├── definitions/            # Event type definitions
│   ├── session_events
│   ├── conversation_events
│   ├── decision_events
│   ├── supervision_events
│   ├── escalation_events
│   └── system_events
├── publishers/             # Event publishing
│   └── event_publisher
├── consumers/              # Event consumption
│   ├── analytics_consumer
│   ├── audit_consumer
│   └── supervisor_consumer
└── routing/                # Event routing rules
    └── event_router
```

---

### 3.8 Knowledge Module (`knowledge/`)

#### Purpose
Knowledge base access and retrieval.

#### Structure
```
knowledge/
├── retrieval/              # Knowledge retrieval
│   ├── knowledge_service   # Retrieval orchestration
│   └── search/             # Search logic
│       ├── semantic_search # Meaning-based search
│       └── keyword_search  # Keyword matching
├── content/                # Content management
│   ├── content_loader      # Content loading
│   └── content_indexer     # Index management
└── sources/                # Knowledge sources
    ├── faq_source
    ├── policy_source
    └── product_source
```

---

### 3.9 Context Module (`context/`)

#### Purpose
Conversation context management.

#### Structure
```
context/
├── context_service         # Context orchestration
├── storage/                # Context storage
│   ├── context_store       # Active context
│   └── context_archive     # Archived context
├── builders/               # Context construction
│   ├── context_builder     # Build context
│   └── summary_builder     # Build summaries
└── providers/              # Context provision
    └── context_provider    # Provide context to agents
```

---

### 3.10 Analytics Module (`analytics/`)

#### Purpose
Metrics collection, aggregation, and reporting.

#### Structure
```
analytics/
├── collection/             # Event collection
│   └── event_collector
├── aggregation/            # Metric aggregation
│   ├── session_metrics
│   ├── conversation_metrics
│   └── escalation_metrics
├── storage/                # Metrics storage
│   └── metrics_store
└── reporting/              # Report generation
    ├── dashboard_provider
    └── report_generator
```

---

### 3.11 Audit Module (`audit/`)

#### Purpose
Compliance logging and audit trail.

#### Structure
```
audit/
├── logging/                # Audit logging
│   ├── audit_logger
│   └── decision_logger
├── storage/                # Audit storage
│   └── audit_store
└── retrieval/              # Audit retrieval
    └── audit_query_service
```

---

### 3.12 Config Module (`config/`)

#### Purpose
Configuration management.

#### Structure
```
config/
├── settings/               # Application settings
│   ├── app_settings
│   ├── agent_settings
│   └── threshold_settings
├── environment/            # Environment configuration
│   └── env_provider
└── feature_flags/          # Feature toggles
    └── feature_flag_provider
```

---

### 3.13 Common Module (`common/`)

#### Purpose
Shared utilities with no domain knowledge.

#### Structure
```
common/
├── utils/                  # Utility functions
│   ├── datetime_utils
│   ├── string_utils
│   └── id_generator
├── logging/                # Logging utilities
│   └── logger
├── validation/             # Validation helpers
│   └── validators
└── errors/                 # Error utilities
    ├── error_handler
    └── error_codes
```

---

### 3.14 Tests Module (`tests/`)

#### Purpose
All test suites.

#### Structure
```
tests/
├── unit/                   # Unit tests
│   ├── agents/             # Agent tests
│   ├── core/               # Core logic tests
│   └── domain/             # Domain tests
├── integration/            # Integration tests
│   ├── services/           # Service integration
│   └── infrastructure/     # Infrastructure integration
├── e2e/                    # End-to-end tests
│   └── scenarios/          # Complete scenarios
├── fixtures/               # Test data
│   ├── sessions/
│   ├── conversations/
│   └── customers/
└── mocks/                  # Mock implementations
    ├── providers/
    └── repositories/
```

---

## 4. Cross-Module Dependency Rules

### 4.1 Allowed Dependencies

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEPENDENCY RULES                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  domain/        →  (nothing - zero dependencies)                │
│                                                                  │
│  core/          →  domain/                                       │
│                                                                  │
│  agents/        →  domain/, core/, common/                       │
│                                                                  │
│  services/      →  domain/, core/, agents/, common/              │
│                                                                  │
│  infrastructure/→  domain/, common/                              │
│                                                                  │
│  api/           →  domain/, services/, common/                   │
│                                                                  │
│  events/        →  domain/, common/                              │
│                                                                  │
│  knowledge/     →  domain/, infrastructure/, common/             │
│                                                                  │
│  context/       →  domain/, infrastructure/, common/             │
│                                                                  │
│  analytics/     →  domain/, events/, infrastructure/, common/    │
│                                                                  │
│  audit/         →  domain/, events/, infrastructure/, common/    │
│                                                                  │
│  config/        →  common/                                       │
│                                                                  │
│  common/        →  (nothing - standalone utilities)              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Forbidden Dependencies

| Module | Cannot Depend On |
|--------|------------------|
| `domain/` | Any other module |
| `core/` | `api/`, `services/`, `infrastructure/`, `agents/` |
| `agents/` | `api/`, `services/`, `infrastructure/` |
| `common/` | Any other module |
| Any module | Circular dependencies |

### 4.3 Dependency Enforcement

| Rule | Enforcement |
|------|-------------|
| Domain isolation | Domain has no imports from other modules |
| Agent isolation | Agents never import from API or infrastructure |
| Infrastructure abstraction | Core/agents use contracts, not implementations |
| Circular prevention | Build fails on circular dependencies |

---

## 5. Agent Isolation from API Logic

### 5.1 Isolation Principle

Agents must be usable without any knowledge of HTTP, WebSocket, or transport.

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT ISOLATION                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  WRONG (Agent knows about API):                                  │
│                                                                  │
│  api/conversation_handler                                        │
│       │                                                          │
│       ▼                                                          │
│  agents/primary/agent                                            │
│       │                                                          │
│       └────► Reads HTTP headers                                  │
│       └────► Knows about request format                          │
│       └────► Returns HTTP status codes                           │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  RIGHT (Agent is transport-agnostic):                            │
│                                                                  │
│  api/conversation_handler                                        │
│       │                                                          │
│       ▼                                                          │
│  services/conversation_service                                   │
│       │                                                          │
│       ▼                                                          │
│  agents/primary/agent                                            │
│       │                                                          │
│       └────► Receives domain objects                             │
│       └────► Makes decisions                                     │
│       └────► Returns domain objects                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Isolation Rules

| Rule | Implementation |
|------|----------------|
| **No transport imports** | Agents never import from `api/` |
| **Domain input/output** | Agents receive and return domain objects |
| **No HTTP awareness** | Agents don't know about status codes, headers, etc. |
| **No direct infrastructure** | Agents use contracts, not implementations |
| **Testable in isolation** | Agents testable with mocked dependencies |

### 5.3 How Services Bridge API and Agents

```
┌─────────────────────────────────────────────────────────────────┐
│                SERVICE BRIDGE PATTERN                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  API Layer (api/):                                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 1. Receive HTTP request                                  │    │
│  │ 2. Validate request structure                            │    │
│  │ 3. Transform DTO → Domain objects                        │    │
│  │ 4. Call service                                          │    │
│  └─────────────────────────┬───────────────────────────────┘    │
│                            │                                     │
│                            ▼                                     │
│  Service Layer (services/):                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 5. Orchestrate operation                                 │    │
│  │ 6. Fetch required data via repositories                  │    │
│  │ 7. Call agent with domain objects                        │    │
│  │ 8. Handle agent response                                 │    │
│  │ 9. Emit events                                           │    │
│  └─────────────────────────┬───────────────────────────────┘    │
│                            │                                     │
│                            ▼                                     │
│  Agent Layer (agents/):                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 10. Receive domain objects                               │    │
│  │ 11. Make decisions                                       │    │
│  │ 12. Return domain result                                 │    │
│  └─────────────────────────┬───────────────────────────────┘    │
│                            │                                     │
│                            ▼                                     │
│  Back through layers:                                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 13. Service processes result                             │    │
│  │ 14. API transforms Domain → DTO                          │    │
│  │ 15. HTTP response returned                               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.4 Agent Contract Example

Agents implement contracts defined in `domain/contracts/`:

```
domain/contracts/agents/primary_agent

Interface: PrimaryAgent
  
  Method: process_turn
    Input:
      - session: Session (domain entity)
      - turn: Turn (domain entity)
      - context: ConversationContext (domain entity)
    Output:
      - AgentResponse (domain entity)
        - response_text: string
        - detected_intent: Intent
        - detected_emotion: Emotion
        - confidence: Confidence
        - action_taken: Action
        - escalation_signal: EscalationSignal (optional)
```

---

## 6. Naming Conventions

### 6.1 Folder and File Naming

| Element | Convention | Example |
|---------|------------|---------|
| Folders | lowercase, snake_case | `session_management/` |
| Files | lowercase, snake_case | `session_service.ext` |
| Test files | `test_` prefix or `_test` suffix | `test_session_service.ext` |

### 6.2 Entity and Class Naming

| Element | Convention | Example |
|---------|------------|---------|
| Entities | PascalCase | `Session`, `Conversation` |
| Value Objects | PascalCase | `SessionId`, `Intent` |
| Services | PascalCase + Service suffix | `SessionService`, `ConversationService` |
| Repositories | PascalCase + Repository suffix | `SessionRepository`, `ContextRepository` |
| Providers | PascalCase + Provider suffix | `AIProvider`, `SpeechProvider` |
| Agents | PascalCase + Agent suffix | `PrimaryAgent`, `SupervisorAgent` |

### 6.3 Contract/Interface Naming

| Element | Convention | Example |
|---------|------------|---------|
| Contracts | PascalCase (no prefix) | `SessionRepository`, `AIProvider` |
| Implementations | PascalCase + Impl suffix | `SessionRepositoryImpl`, `AIProviderImpl` |

### 6.4 Event Naming

| Element | Convention | Example |
|---------|------------|---------|
| Event types | SCREAMING_SNAKE_CASE | `SESSION_STARTED`, `INTENT_DETECTED` |
| Event classes | PascalCase + Event suffix | `SessionStartedEvent`, `IntentDetectedEvent` |

### 6.5 Variable and Parameter Naming

| Element | Convention | Example |
|---------|------------|---------|
| Variables | snake_case | `session_id`, `turn_count` |
| Constants | SCREAMING_SNAKE_CASE | `MAX_TURN_COUNT`, `DEFAULT_TIMEOUT` |
| Boolean variables | is_/has_/can_ prefix | `is_authenticated`, `has_profile` |

---

## 7. Module Communication Patterns

### 7.1 Inward Dependencies via Contracts

```
┌─────────────────────────────────────────────────────────────────┐
│              CONTRACT-BASED DEPENDENCIES                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  services/session/session_service                                │
│       │                                                          │
│       │  Uses contract:                                          │
│       │  domain/contracts/repositories/session_repository        │
│       │                                                          │
│       │  Does NOT import:                                        │
│       │  infrastructure/persistence/session/session_repo_impl    │
│       │                                                          │
│       ▼                                                          │
│  At runtime, implementation is injected                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Event-Based Communication

```
┌─────────────────────────────────────────────────────────────────┐
│              EVENT-BASED COMMUNICATION                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  services/conversation_service                                   │
│       │                                                          │
│       │  Emits event via:                                        │
│       │  domain/contracts/services/event_publisher               │
│       │                                                          │
│       ▼                                                          │
│  events/publishers/event_publisher (implements contract)        │
│       │                                                          │
│       ▼                                                          │
│  Event delivered to consumers                                    │
│       │                                                          │
│       ├───► analytics/collection/event_collector                │
│       ├───► audit/logging/audit_logger                          │
│       └───► agents/supervisor/agent (via supervisor_service)    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Testing Strategy by Module

### 8.1 Test Types by Module

| Module | Primary Test Type | What to Test |
|--------|-------------------|--------------|
| `domain/` | Unit | Entity validation, value object behavior |
| `core/` | Unit | Business rules, calculations |
| `agents/` | Unit + Integration | Decision logic, agent contracts |
| `services/` | Integration | Orchestration, multi-step operations |
| `api/` | Integration + E2E | Request/response handling |
| `infrastructure/` | Integration | External system interaction |

### 8.2 Agent Testing

Agents are tested in isolation using mocked dependencies:

```
tests/unit/agents/primary/
├── test_intent_detection      # Test intent classification
├── test_emotion_detection     # Test emotion assessment
├── test_confidence_scoring    # Test confidence calculation
├── test_response_generation   # Test response creation
└── test_escalation_decision   # Test escalation logic
```

---

## 9. Summary

### 9.1 Module Quick Reference

| Module | Purpose | Dependencies |
|--------|---------|--------------|
| `api/` | HTTP/WS handling | services/, domain/, common/ |
| `services/` | Orchestration | agents/, core/, domain/, common/ |
| `agents/` | AI decisions | core/, domain/, common/ |
| `core/` | Business logic | domain/ |
| `domain/` | Entities, contracts | (none) |
| `infrastructure/` | External systems | domain/, common/ |
| `events/` | Event management | domain/, common/ |
| `knowledge/` | Knowledge retrieval | domain/, infrastructure/, common/ |
| `context/` | Context management | domain/, infrastructure/, common/ |
| `analytics/` | Metrics | domain/, events/, infrastructure/ |
| `audit/` | Compliance | domain/, events/, infrastructure/ |
| `config/` | Configuration | common/ |
| `common/` | Utilities | (none) |

### 9.2 Key Isolation Rules

| Rule | Enforcement |
|------|-------------|
| Agents don't know about HTTP | No imports from `api/` in `agents/` |
| Domain has no dependencies | No imports in `domain/` |
| Infrastructure implements contracts | `infrastructure/` imports from `domain/contracts/` |
| No circular dependencies | Build fails on cycles |

---

## Appendix A: Dependency Diagram

```
                         ┌─────────┐
                         │  api/   │
                         └────┬────┘
                              │
                              ▼
                       ┌───────────┐
                       │ services/ │
                       └─────┬─────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │ agents/  │   │   core/  │   │knowledge/│
        └────┬─────┘   └────┬─────┘   └────┬─────┘
             │              │              │
             └──────────────┼──────────────┘
                            │
                            ▼
                      ┌──────────┐
                      │ domain/  │
                      └──────────┘
                            ▲
                            │
                   ┌────────┴────────┐
                   │                 │
            ┌──────────────┐   ┌──────────┐
            │infrastructure│   │  common/ │
            └──────────────┘   └──────────┘
```

---

## Appendix B: Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-17 | Backend Architecture | Initial codebase blueprint |

---

*This blueprint provides the structure for a maintainable, testable, and scalable backend codebase. Follow these conventions to ensure consistent organization and clear boundaries between components.*

# AI-Powered Digital Call Center - Backend

This directory contains the backend services for the AI-Powered Digital Call Center.

## Structure

```
backend/
├── app/
│   ├── api/           # API endpoints and request handlers
│   ├── agents/        # Autonomous AI agent modules
│   ├── core/          # Core business logic and configuration
│   ├── services/      # Backend services (routing, session, etc.)
│   ├── memory/        # Context and memory management
│   ├── analytics/     # Analytics and monitoring
│   ├── integrations/  # External system integrations
│   └── main.py        # Application entry point
├── tests/             # Test suites
└── README.md          # This file
```

## Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `api/` | HTTP/WebSocket endpoints, request validation, response formatting |
| `agents/` | Primary, Supervisor, and Escalation agent logic |
| `core/` | Configuration, constants, shared utilities |
| `services/` | Call routing, session management, queue handling |
| `memory/` | Conversation context, short-term and long-term memory |
| `analytics/` | Metrics collection, reporting, audit logging |
| `integrations/` | CRM, ticketing, enterprise system adapters |

## Design Principles

- **Separation of Concerns**: Each module has a single, well-defined responsibility
- **Agent Isolation**: Agent logic is decoupled from API concerns
- **Event-Driven**: Services communicate through events where appropriate
- **Testability**: All modules are designed for independent testing

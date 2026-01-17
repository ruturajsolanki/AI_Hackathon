# AI Call Center - Frontend

Modern dashboard UI for the AI-Powered Digital Call Center.

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **React Router** - Client-side routing
- **Lucide React** - Icon library
- **CSS Modules** - Scoped styling

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── layout/          # App shell components
│   │   │   ├── AppLayout    # Main layout wrapper
│   │   │   ├── Sidebar      # Navigation sidebar
│   │   │   └── Header       # Top header bar
│   │   ├── dashboard/       # Dashboard components
│   │   │   ├── DashboardPage
│   │   │   ├── ActivityFeed
│   │   │   └── AgentStatus
│   │   ├── chat/            # Demo chat components
│   │   │   ├── ChatDemoPage
│   │   │   ├── ChatMessage
│   │   │   └── AgentInsights
│   │   └── common/          # Reusable components
│   │       ├── Card
│   │       ├── StatCard
│   │       └── Badge
│   ├── hooks/               # Custom React hooks
│   │   ├── useInteraction   # Interaction management
│   │   └── useRealtimeUpdates
│   ├── services/            # API & WebSocket clients
│   │   ├── api.ts
│   │   └── websocket.ts
│   ├── types/               # TypeScript definitions
│   ├── styles/              # Global styles & CSS vars
│   └── assets/              # Static assets
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## Getting Started

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Design System

### Colors (Dark Theme)

| Variable | Purpose |
|----------|---------|
| `--color-bg-primary` | Main background |
| `--color-bg-secondary` | Card backgrounds |
| `--color-accent-primary` | Cyan accent |
| `--color-accent-secondary` | Purple accent |
| `--color-accent-success` | Green status |
| `--color-accent-warning` | Yellow alerts |
| `--color-accent-danger` | Red errors |

### Typography

- **Font Sans**: DM Sans
- **Font Mono**: JetBrains Mono

### Components

- **Card**: Container with optional header
- **StatCard**: Metric display with trend
- **Badge**: Status indicators

## Pages

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | DashboardPage | Real-time metrics overview |
| `/demo` | ChatDemoPage | Interactive demo |

## Real-time Updates

The frontend is designed for real-time updates via WebSocket:

```typescript
// Subscribe to events
const { events, isConnected } = useRealtimeUpdates([
  'interaction_started',
  'message_received',
  'decision_made',
])
```

## API Integration

Services are designed for easy backend connection:

```typescript
// Start interaction
await api.startInteraction({ channel: 'chat' })

// Send message
await api.sendMessage({ interactionId, content })

// End interaction
await api.endInteraction({ interactionId })
```

## Development Notes

- Currently uses simulated responses for demo
- WebSocket service is stubbed for future implementation
- CSS Modules for component-scoped styling
- Responsive design with mobile breakpoints

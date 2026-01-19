# 🤖 AI-Powered Digital Call Center

An autonomous AI call center that handles customer inquiries through voice and chat, using multi-agent architecture with intelligent escalation to human agents.

[![Demo Video](https://img.shields.io/badge/Demo-Watch%20on%20Loom-blueviolet?style=for-the-badge&logo=loom)](https://www.loom.com/share/6d098f0c010748d4a483afed996d1822)
[![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square&logo=python)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61dafb?style=flat-square&logo=react)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)

---

## 🎬 Demo Video

<a href="https://www.loom.com/share/6d098f0c010748d4a483afed996d1822">
  <img src="https://cdn.loom.com/sessions/thumbnails/6d098f0c010748d4a483afed996d1822-with-play.gif" alt="AI Call Center Demo" width="600">
</a>

👉 **[Watch Full Demo on Loom](https://www.loom.com/share/6d098f0c010748d4a483afed996d1822)**

---

## 🎯 Problem Statement

Traditional call centers face significant challenges:
- **High costs**: $25-35 per call with human agents
- **Long wait times**: Customers wait 5-15 minutes
- **Inconsistent quality**: Service varies by agent and time
- **24/7 staffing**: Expensive to maintain round-the-clock coverage

**Our Solution**: An AI-powered call center that autonomously handles 80% of routine inquiries while intelligently escalating complex cases to humans.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🤖 **Multi-Agent Architecture** | Primary, Supervisor, and Escalation agents work in pipeline |
| 🎙️ **Voice + Chat Support** | Browser-based voice with real-time waveform visualization |
| 📊 **Real Data Integration** | Looks up actual orders, customers, products from database |
| 🧠 **Semantic Search** | Sentence-transformer embeddings for intelligent KB search |
| 🔒 **Safety Guardrails** | Auto-escalate on legal mentions, threats, low confidence |
| 📈 **Analytics Dashboard** | Track resolution rates, response times, sentiment trends |
| 🔄 **Multi-LLM Support** | OpenAI, Google Gemini, or local Ollama models |
| 👤 **Human Handoff** | Seamless escalation with full conversation context |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + Vite)                  │
│  Call Simulator │ Analytics │ Interactions │ Agent Studio   │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTPS/REST
┌────────────────────────────┴────────────────────────────────┐
│                    BACKEND (FastAPI)                        │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Call Orchestrator                      │    │
│  └──────┬─────────────────┬─────────────────┬──────────┘    │
│         │                 │                 │               │
│  ┌──────┴──────┐  ┌───────┴───────┐  ┌──────┴──────┐        │
│  │   PRIMARY   │  │  SUPERVISOR   │  │  ESCALATION │        │
│  │    AGENT    │  │    AGENT      │  │    AGENT    │        │
│  │  • Intent   │  │  • Quality    │  │  • Routing  │        │
│  │  • Emotion  │  │  • Compliance │  │  • Tickets  │        │
│  │  • Response │  │  • Tone       │  │  • Handoff  │        │
│  └─────────────┘  └───────────────┘  └─────────────┘        │
│                             │                               │
│  ┌──────────────────────────┴───────────────────────────┐   │
│  │  Knowledge Base (Semantic) │ LLM Layer │ Persistence │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Ollama (for local LLM) or OpenAI/Gemini API key

### Installation

```bash
# Clone the repository
git clone https://github.com/ruturajsolanki/AI_Hackathon.git
cd AI_Hackathon/ai-call-center

# Backend setup
cd backend
pip install -r requirements.txt
cp .env.example .env  # Configure your API keys

# Start backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev
```

### Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Demo Credentials
```
Email: demo@example.com
Password: demo123
```

---

## 📁 Project Structure

```
ai-call-center/
├── backend/
│   ├── app/
│   │   ├── agents/          # AI agents (Primary, Supervisor, Escalation)
│   │   ├── api/             # FastAPI endpoints
│   │   ├── core/            # Config, models, LLM integration
│   │   ├── services/        # Orchestrator, Knowledge Base
│   │   ├── memory/          # Conversation context
│   │   └── persistence/     # Database (Supabase/MongoDB/SQLite)
│   ├── data/                # Sample data (orders, products, FAQs)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── services/        # API client
│   │   └── hooks/           # Custom hooks (speech, etc.)
│   └── package.json
└── docs/                    # Documentation & diagrams
```

---

## 🎮 Demo Scenarios

### ✅ Successful Resolution
```
Customer: "What's the status of my order ORD10024?"
AI: Looks up real order data → "Your order is SHIPPED. 
    Tracking: 1Z999AA10123456799. Delivery: Feb 5th."
Result: Resolved in ~12 seconds
```

### 🔴 Intelligent Escalation
```
Customer: "I've been waiting 3 weeks for my refund! 
          I want to speak to a manager NOW!"
AI: Detects frustration + escalation trigger → 
    Creates ticket → Routes to human agent
Result: Seamless handoff with full context
```

---

## 🔧 Configuration

### LLM Providers

| Provider | Setup |
|----------|-------|
| **Ollama** | `OLLAMA_HOST=http://localhost:11434` |
| **OpenAI** | `OPENAI_API_KEY=sk-...` |
| **Gemini** | `GEMINI_API_KEY=...` |

### Environment Variables

```env
# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key

# LLM (choose one)
OPENAI_API_KEY=sk-your-key
GEMINI_API_KEY=your-gemini-key
OLLAMA_HOST=http://localhost:11434

# CORS
CORS_ORIGINS=http://localhost:3000,https://your-frontend.com
```

---

## 📊 Tech Stack

| Layer | Technologies |
|-------|--------------|
| **Frontend** | React 18, Vite, TypeScript, CSS Modules |
| **Backend** | FastAPI, Python 3.9+, Pydantic v2 |
| **AI/ML** | sentence-transformers, OpenAI, Gemini, Ollama |
| **Database** | Supabase (PostgreSQL), MongoDB, SQLite |
| **Voice** | Web Speech API (browser-native) |
| **Deployment** | Railway, Docker |

---

## 🏆 What Makes This Different?

| Traditional Chatbot | Our AI Call Center |
|--------------------|--------------------|
| Canned responses | Real database lookups |
| Forgets context | Remembers conversation |
| No emotion detection | Tracks sentiment trajectory |
| Basic keyword matching | Semantic understanding |
| Black box | Full transparency & audit |
| Single LLM locked | Multi-provider support |

---

## 📈 Business Impact

| Metric | Traditional | With AI |
|--------|-------------|---------|
| Cost per call | $25-35 | $3-5 |
| Wait time | 5-15 min | 0 seconds |
| Resolution time | 8-12 min | 30-60 sec |
| 24/7 availability | $$$$$ | Included |

---

## 📄 Documentation

- [Complete Demo Script](ai-call-center/docs/COMPLETE_DEMO_PRESENTATION.md)
- [Submission Document](ai-call-center/docs/SUBMISSION_DOCUMENT.md)
- [Deployment Guide](ai-call-center/docs/DEPLOYMENT_RAILWAY.md)
- [Architecture Diagrams](ai-call-center/docs/diagrams/)

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License.

---

## 👨‍💻 Author

**Ruturaj Solanki**

[![GitHub](https://img.shields.io/badge/GitHub-ruturajsolanki-181717?style=flat-square&logo=github)](https://github.com/ruturajsolanki)

---

<p align="center">
  <b>⭐ Star this repo if you found it helpful!</b>
</p>

# Setup Guide

## AI-Powered Digital Call Center - Complete Setup Instructions

---

## Quick Start (Default - SQLite, No Auth)

If you just want to run the app locally without MongoDB:

```bash
# Backend
cd ai-call-center/backend
pip3 install -r requirements.txt
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (new terminal)
cd ai-call-center/frontend
npm install
npm run dev
```

The app will use SQLite for persistence (in-memory) and no authentication by default.

---

## Full Setup with MongoDB

### 1. Install MongoDB

**macOS (Homebrew):**
```bash
brew tap mongodb/brew
brew install mongodb-community@7.0
brew services start mongodb-community@7.0
```

**Ubuntu/Debian:**
```bash
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod
```

**Docker:**
```bash
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password123 \
  -v mongodb_data:/data/db \
  mongo:7.0
```

### 2. Configure MongoDB Connection

Create a `.env` file in the backend directory:

```bash
cd ai-call-center/backend
touch .env
```

Add the following to `.env`:

```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=ai_call_center

# For Docker with auth:
# MONGODB_URI=mongodb://admin:password123@localhost:27017

# For MongoDB Atlas (cloud):
# MONGODB_URI=mongodb+srv://username:password@cluster.xxxxx.mongodb.net

# OpenAI API Key (optional - can be set via Settings UI)
OPENAI_API_KEY=sk-your-key-here

# App Settings
DEBUG=true
APP_ENV=development
```

### 3. Install Backend Dependencies

```bash
cd ai-call-center/backend
pip3 install -r requirements.txt
```

This installs:
- `motor` - Async MongoDB driver
- `pymongo` - MongoDB driver
- `python-jose` - JWT tokens
- `passlib` - Password hashing
- `python-multipart` - Form data support

### 4. Run the Backend

```bash
cd ai-call-center/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Check the health endpoint:
```bash
curl http://localhost:8000/health
```

You should see:
```json
{
  "status": "healthy",
  "timestamp": "...",
  "version": "0.1.0",
  "database": "mongodb"  // or "sqlite" if MongoDB not connected
}
```

### 5. Run the Frontend

```bash
cd ai-call-center/frontend
npm install
npm run dev
```

---

## Authentication

### Demo User

A demo user is automatically created:
- **Email:** `demo@example.com`
- **Password:** `demo123`

### Login via API

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo@example.com&password=demo123"

# Response:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Using the Token

```bash
# Get current user info
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Register New User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword",
    "full_name": "New User"
  }'
```

---

## OpenAI API Key Setup

### Option 1: Via Settings UI (Recommended)

1. Open the app at http://localhost:3000
2. Go to **Settings** (sidebar)
3. Find **AI Configuration** section
4. Paste your OpenAI API key
5. Click **Set Key**
6. The status will show "Connected" if valid

### Option 2: Via Environment Variable

Add to your `.env` file:
```env
OPENAI_API_KEY=sk-your-api-key-here
```

### Option 3: Via API

```bash
curl -X POST http://localhost:8000/api/config/llm \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "sk-your-api-key-here",
    "provider": "openai"
  }'
```

---

## Agent Programming (Agent Studio)

### Access

1. Open http://localhost:3000
2. Click **Agent Studio** in the sidebar
3. Select an agent from the left panel
4. Edit prompts and settings in the main area

### What You Can Configure

| Agent | What It Does | Key Settings |
|-------|--------------|--------------|
| **Primary** | First response to customer | System prompt, intent detection, emotion assessment |
| **Supervisor** | Reviews Primary's response | Quality criteria, compliance rules, tone checks |
| **Escalation** | Decides when to escalate | Escalation thresholds, human handoff rules |

### Testing Prompts

1. Make your changes to the prompt
2. Enter a test message in the "Test Prompt" section
3. Click "Run Test"
4. View the LLM output and latency

### Saving Changes

1. Make your edits
2. Click **Save Changes** (top right)
3. Changes take effect immediately for new interactions

### Reset to Defaults

If you break something:
1. Click **Reset to Default** in the sidebar
2. Confirm the action
3. Original prompts are restored

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGODB_DATABASE` | `ai_call_center` | Database name |
| `OPENAI_API_KEY` | None | OpenAI API key |
| `DEBUG` | `true` | Enable debug mode |
| `APP_ENV` | `development` | Environment (development/staging/production) |
| `SECRET_KEY` | (hardcoded) | JWT signing key (change in production!) |

---

## Troubleshooting

### MongoDB Not Connecting

```bash
# Check if MongoDB is running
brew services list | grep mongodb  # macOS
sudo systemctl status mongod       # Linux

# Test connection
mongosh mongodb://localhost:27017
```

### "Auth Not Available" Error

Install the auth dependencies:
```bash
pip3 install python-jose[cryptography] passlib[bcrypt] python-multipart
```

### Agent Programming Shows Empty Cards

The frontend needs to refresh. Try:
1. Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
2. Clear browser cache
3. Restart the frontend dev server

### OpenAI API Errors

1. Check your API key is valid at https://platform.openai.com/api-keys
2. Ensure you have credits/billing set up
3. Check the API key in Settings shows "Connected"

---

## Production Deployment Notes

### Security Checklist

- [ ] Change `SECRET_KEY` to a secure random value
- [ ] Use MongoDB with authentication enabled
- [ ] Enable HTTPS
- [ ] Set `DEBUG=false`
- [ ] Store secrets in environment variables, not code
- [ ] Add rate limiting
- [ ] Enable CORS only for your domain

### MongoDB Atlas (Cloud)

For production, use MongoDB Atlas:

1. Create account at https://cloud.mongodb.com
2. Create a cluster
3. Get connection string
4. Set `MONGODB_URI` in your environment

### Docker Deployment

See `docker-compose.yml` for containerized deployment (coming soon).

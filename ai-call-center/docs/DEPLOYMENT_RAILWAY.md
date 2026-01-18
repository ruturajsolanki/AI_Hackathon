# Railway Deployment Guide

## AI-Powered Digital Call Center - Live Deployment

---

## Prerequisites

1. GitHub account with your code pushed
2. Railway account (https://railway.app - sign up with GitHub)
3. Supabase project already set up (for database)
4. LLM API key (OpenAI/Gemini) or Ollama server accessible from internet

---

## Step 1: Deploy Backend

### 1.1 Create New Project

1. Go to **https://railway.app/dashboard**
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your repository: `AI_Hackathon`
5. Select the `ai-call-center/backend` folder

### 1.2 Configure Environment Variables

In Railway dashboard, go to **Variables** tab and add:

```
# Required
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1...

# LLM Configuration (choose one)
OPENAI_API_KEY=sk-your-key
# OR
GEMINI_API_KEY=your-gemini-key

# App Settings
DEBUG=false
CORS_ORIGINS=https://your-frontend.railway.app,https://your-frontend.vercel.app
```

### 1.3 Set Root Directory

In **Settings** tab:
- Set **Root Directory** to: `ai-call-center/backend`

### 1.4 Deploy

Click **Deploy** - Railway will:
1. Detect Python project
2. Install requirements.txt
3. Run uvicorn server

### 1.5 Get Backend URL

After deployment, click **Settings** → **Domains** → **Generate Domain**

Your backend URL will be: `https://your-backend.up.railway.app`

---

## Step 2: Deploy Frontend

### 2.1 Create Another Service

In same project, click **"New"** → **"GitHub Repo"** → Select same repo

### 2.2 Configure Frontend

In **Settings** tab:
- Set **Root Directory** to: `ai-call-center/frontend`

### 2.3 Add Environment Variables

```
VITE_API_URL=https://your-backend.up.railway.app
```

### 2.4 Generate Frontend Domain

**Settings** → **Domains** → **Generate Domain**

Your frontend URL: `https://your-frontend.up.railway.app`

---

## Step 3: Update CORS

Go back to your **backend** service and update:

```
CORS_ORIGINS=https://your-frontend.up.railway.app
```

---

## Alternative: Vercel for Frontend (Better Performance)

### Frontend on Vercel (Free)

1. Go to **https://vercel.com**
2. Import GitHub repo
3. Set **Root Directory**: `ai-call-center/frontend`
4. Add Environment Variable:
   - `VITE_API_URL` = `https://your-backend.up.railway.app`
5. Deploy

Vercel provides:
- Faster CDN
- Better caching
- Free SSL
- Custom domains

---

## Deployment Checklist

- [ ] Backend deployed on Railway
- [ ] Environment variables set (Supabase, LLM keys)
- [ ] CORS configured with frontend URL
- [ ] Frontend deployed (Railway or Vercel)
- [ ] VITE_API_URL points to backend
- [ ] Test /health endpoint: `curl https://your-backend.up.railway.app/health`
- [ ] Test login with demo@example.com / demo123

---

## Troubleshooting

### Backend won't start
```bash
# Check logs in Railway dashboard
# Common issues:
# - Missing environment variables
# - Python version mismatch
# - Import errors
```

### CORS errors
```bash
# Ensure CORS_ORIGINS includes your frontend URL
# No trailing slash!
CORS_ORIGINS=https://your-frontend.up.railway.app
```

### LLM not working
```bash
# For cloud LLMs: Check API key is set
# For Ollama: Ollama server must be publicly accessible
# Use cloud LLM (OpenAI/Gemini) for production
```

---

## Cost Estimation

| Service | Free Tier | Paid |
|---------|-----------|------|
| Railway | $5/month credit | ~$5-20/month |
| Vercel | Unlimited | Free for demos |
| Supabase | 500MB, 2 projects | Free for demos |
| OpenAI | Pay per use | ~$0.01-0.03/call |

**For hackathon demo: FREE** (within free tier limits)

---

## Quick Deploy Commands

```bash
# Push latest changes
cd /Users/ruturajsolanki/Desktop/AI_Hackathon
git add -A
git commit -m "Add Railway deployment config"
git push origin main

# Railway CLI (optional)
npm install -g @railway/cli
railway login
railway link
railway up
```

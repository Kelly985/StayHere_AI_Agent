# 🔧 Render Environment Variables Fix

## Issue
Your app is deployed successfully but getting 401 Unauthorized errors because the environment variables in Render don't match what your application expects.

**Your app expects**: `OPENROUTER_API_KEY`
**Render probably has**: `TOGETHER_API_KEY` or nothing

## Quick Fix Steps

### 1. Go to Render Dashboard
- Visit: https://dashboard.render.com
- Click on your deployed service

### 2. Update Environment Variables
- Click **"Environment"** in left sidebar
- **DELETE** any `TOGETHER_API_KEY` if it exists
- **ADD** these variables:

| Variable | Value |
|----------|-------|
| `OPENROUTER_API_KEY` | `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` |
| `OPENROUTER_MODEL` | `x-ai/grok-4-fast:free` |

### 3. Save & Wait
- Click **"Save Changes"**
- Render will redeploy automatically (1-2 minutes)

## Verification
After redeployment, test your API:
- The 401 Unauthorized error should disappear
- Your AI agent should respond properly

## Complete Environment Variables List
Make sure you have all these in Render:

```
OPENROUTER_API_KEY=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
OPENROUTER_MODEL=x-ai/grok-4-fast:free
API_HOST=0.0.0.0
DEBUG=false
KNOWLEDGE_BASE_PATH=./knowledgebase
MAX_CONTEXT_LENGTH=4000
APP_NAME=Kenyan Real Estate AI Agent
APP_VERSION=1.0.0
```

## Alternative Solution
If you prefer, you can:
1. Delete the current service in Render
2. Create a new service from your repo
3. The new `render.yaml` will configure everything automatically

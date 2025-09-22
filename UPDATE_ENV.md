# Environment Configuration Update

## Updated .env File for OpenRouter

Please update your `.env` file with the following content to use OpenRouter instead of Together AI:

```env
# Kenyan Real Estate AI Agent Configuration - OpenRouter Version

# OpenRouter AI Configuration
OPENROUTER_API_KEY=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
OPENROUTER_MODEL=x-ai/grok-4-fast:free

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Knowledge Base Configuration
KNOWLEDGE_BASE_PATH=./knowledgebase
MAX_CONTEXT_LENGTH=4000

# Application Settings
APP_NAME=Kenyan Real Estate AI Agent
APP_VERSION=1.0.0
CORS_ORIGINS=["*"]
```

## Key Changes:
1. **TOGETHER_API_KEY** → **OPENROUTER_API_KEY**
2. **TOGETHER_MODEL** → **OPENROUTER_MODEL** 
3. Model changed from `deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free` to `x-ai/grok-4-fast:free`

## Alternative:
If you don't have a `.env` file, the application will automatically use the hardcoded values from `run.py` with your new OpenRouter configuration.

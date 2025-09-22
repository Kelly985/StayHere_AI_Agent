"""
Application runner for Kenyan Real Estate AI Agent
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables from file if .env doesn't exist
env_file = project_root / ".env"
if not env_file.exists():
    # Set default environment variables
    os.environ.setdefault("OPENROUTER_API_KEY", "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")
    os.environ.setdefault("OPENROUTER_MODEL", "x-ai/grok-4-fast:free")
    os.environ.setdefault("API_HOST", "0.0.0.0")
    os.environ.setdefault("API_PORT", "8000")
    os.environ.setdefault("DEBUG", "True")
    os.environ.setdefault("KNOWLEDGE_BASE_PATH", "./knowledgebase")
    os.environ.setdefault("MAX_CONTEXT_LENGTH", "4000")
    os.environ.setdefault("APP_NAME", "Kenyan Real Estate AI Agent")
    os.environ.setdefault("APP_VERSION", "1.0.0")

if __name__ == "__main__":
    import uvicorn
    from config.settings import settings
    from app.logging_config import setup_logging, get_logger
    
    # Initialize logging first
    setup_logging(log_level=settings.debug and "DEBUG" or "INFO")
    logger = get_logger(__name__)
    
    logger.info(f"Starting {settings.app_name} v{settings.app_version}", extra={
        'app_name': settings.app_name,
        'app_version': settings.app_version,
        'api_host': settings.api_host,
        'api_port': settings.api_port,
        'debug_mode': settings.debug
    })
    
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Server will be available at: http://{settings.api_host}:{settings.api_port}")
    print(f"API Documentation: http://{settings.api_host}:{settings.api_port}/docs")
    print(f"Logs will be stored in: ./logs/")
    print(f"Log Level: {'DEBUG' if settings.debug else 'INFO'}")
    
    try:
        uvicorn.run(
            "app.main:app",
            host=settings.api_host,
            port=settings.api_port,
            reload=settings.debug,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error("Application failed to start", extra={'error': str(e)}, exc_info=True)
        raise

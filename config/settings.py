"""
Configuration settings for Kenyan Real Estate AI Agent
"""
import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # OpenRouter AI Configuration - SECURE WITH ENVIRONMENT VARIABLES
    openrouter_api_key: str = Field(
        default="",
        env="OPENROUTER_API_KEY",
        description="OpenRouter API key - NEVER hardcode this!"
    )
    openrouter_model: str = Field(
        default="x-ai/grok-4-fast:free",
        env="OPENROUTER_MODEL"
    )
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # Knowledge Base Configuration
    knowledge_base_path: str = "./knowledgebase"
    max_context_length: int = 4000
    
    # Application Settings
    app_name: str = "Kenyan Real Estate AI Agent"
    app_version: str = "1.0.0"
    cors_origins: List[str] = ["*"]
    
    # File Processing
    supported_file_types: List[str] = [".txt", ".pdf", ".docx"]
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    
    # Vector Database Settings
    vector_dimension: int = 384  # For sentence-transformers/all-MiniLM-L6-v2
    similarity_threshold: float = 0.7
    max_search_results: int = 10
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from old configuration


# Global settings instance
settings = Settings()

# Ensure knowledge base directory exists
knowledge_base_dir = Path(settings.knowledge_base_path)
knowledge_base_dir.mkdir(exist_ok=True)

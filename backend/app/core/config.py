"""Application configuration."""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings."""
    
    # App
    APP_NAME: str = "AI Kubernetes Agent"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # OpenRouter
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "openai/gpt-4-turbo"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    
    # Kubernetes
    KUBECONFIG_PATH: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

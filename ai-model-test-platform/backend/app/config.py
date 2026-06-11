from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:////opt/ai-model-test-platform/backend/ai_test.db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_tls: bool = True
    
    # App
    app_name: str = "AI Model Test Platform"
    debug: bool = True
    secret_key: str = "your-secret-key-change-in-production"
    
    # LLM
    default_llm_timeout: int = 30
    
    class Config:
        env_file = ".env"


settings = Settings()

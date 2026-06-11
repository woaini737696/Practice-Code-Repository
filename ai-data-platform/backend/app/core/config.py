from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "AI数据分析中台"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-this-secret-key"

    # MySQL 只读从库配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = ""
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = ""

    # SQLite 本地数据库
    SQLITE_PATH: str = "./data/platform.db"

    # LLM 配置
    LLM_PROVIDER: str = "deepseek"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "deepseek-chat"
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"

    # 查询安全限制
    MAX_QUERY_TIMEOUT: int = 30
    MAX_QUERY_ROWS: int = 10000
    MAX_QUERY_PER_MINUTE: int = 60

    # 邮件告警配置
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    ALERT_FROM_EMAIL: Optional[str] = None
    ALERT_TO_EMAIL: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

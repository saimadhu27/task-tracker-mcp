from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

ROOT = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")
    database_url: str
    dev_user_email: str = "dev@example.com"
    app_timezone: str = "America/Los_Angeles"
    
    server_transport: Literal["stdio", "streamable-http"] = "stdio"
    server_host: str = "127.0.0.1"
    server_port: int = 8000
    log_level: str = "INFO"
    log_format: Literal["text", "json"] = "text"
    
    # "none" = local development (stdio, or HTTP on loopback only). "api_key" = every
    # HTTP request must carry a valid API key.
    auth_mode: Literal["none", "api_key"] = "none"
    public_base_url: str = "http://127.0.0.1:8000"
    rate_limit_per_minute: int = 60
    
settings = Settings()


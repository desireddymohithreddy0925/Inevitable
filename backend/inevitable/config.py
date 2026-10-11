from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class Settings(BaseSettings):
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    backend_cors_origins: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    gemma_provider: str = "mock"
    together_api_key: Optional[str] = None
    gemma_model_id: Optional[str] = None
    model_timeout: int = 120
    model_max_retries: int = 3
    
    enable_untrusted_execution: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

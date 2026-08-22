from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "ai-kubernetes-agent"
    kubeconfig_path: str = str(Path.home() / ".kube" / "config")
    kubectl_timeout_seconds: int = 30

    # Local-only reasoning. Optional Ollama; heuristic engine always available.
    llm_provider: str = "local"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2"
    ollama_timeout_seconds: int = 60

    auth_secret: str = "local-dev-secret-change-me"
    demo_username: str = "admin"
    demo_password: str = "admin"

    database_path: str = str(Path(__file__).resolve().parents[2] / "data" / "agent.db")
    demo_mode: bool = False

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()

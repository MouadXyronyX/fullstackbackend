from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Al-Quds-Furniture"
    debug: bool = True

    # Database — defaults to SQLite for local dev
    database_url: str = "sqlite:///./alquds_store.db"

    # Supabase (REST API — no direct PG connection needed)
    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_anon_key: str = ""

    # Redis (optional — code handles it being missing locally)
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Admin
    admin_secret_route: str = "portal-x9k2"

    # Frontend
    frontend_url: str = "http://localhost:5173"

    # GitHub Storage (for product images)
    github_token: str = ""
    github_repo_owner: str = ""
    github_repo_name: str = ""
    github_branch: str = "main"

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache()
def get_settings():
    return Settings()

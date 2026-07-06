import os


def _env(name: str, default: str = "") -> str:
    """Env var, treating blank values (e.g. 'KEY=' lines in a .env) as unset."""
    value = os.environ.get(name, "").strip()
    return value or default


class Settings:
    """All runtime configuration comes from environment variables (see .env.example)."""

    def __init__(self) -> None:
        self.openrouter_api_key: str = _env("OPENROUTER_API_KEY")
        self.llm_model: str = _env("LLM_MODEL", "anthropic/claude-sonnet-4.5")
        self.llm_base_url: str = _env("LLM_BASE_URL", "https://openrouter.ai/api/v1")
        self.outscraper_api_key: str = _env("OUTSCRAPER_API_KEY")
        self.database_url: str = _env("DATABASE_URL", "sqlite:///repdefense.db")
        self.admin_token: str = _env("ADMIN_TOKEN", "change-me")
        self.max_reviews_per_audit: int = int(_env("MAX_REVIEWS_PER_AUDIT", "200"))
        self.competitor_review_sample: int = int(_env("COMPETITOR_REVIEW_SAMPLE", "60"))

    @property
    def live_collection_enabled(self) -> bool:
        return bool(self.outscraper_api_key)

    @property
    def live_analysis_enabled(self) -> bool:
        return bool(self.openrouter_api_key)


settings = Settings()

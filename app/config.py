import os


class Settings:
    """All runtime configuration comes from environment variables (see .env.example)."""

    def __init__(self) -> None:
        self.openrouter_api_key: str = os.environ.get("OPENROUTER_API_KEY", "")
        self.llm_model: str = os.environ.get("LLM_MODEL", "anthropic/claude-sonnet-4.5")
        self.llm_base_url: str = os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1")
        self.outscraper_api_key: str = os.environ.get("OUTSCRAPER_API_KEY", "")
        self.database_url: str = os.environ.get("DATABASE_URL", "sqlite:///repdefense.db")
        self.admin_token: str = os.environ.get("ADMIN_TOKEN", "change-me")
        self.max_reviews_per_audit: int = int(os.environ.get("MAX_REVIEWS_PER_AUDIT", "200"))
        self.competitor_review_sample: int = int(os.environ.get("COMPETITOR_REVIEW_SAMPLE", "60"))

    @property
    def live_collection_enabled(self) -> bool:
        return bool(self.outscraper_api_key)

    @property
    def live_analysis_enabled(self) -> bool:
        return bool(self.openrouter_api_key)


settings = Settings()

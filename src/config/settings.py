"""Pydantic Settings for environment configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/yurei_db"

    # Analysis Loop
    analysis_interval_seconds: int = 30
    lookback_minutes: int = 20

    # Volume Spike Detection
    volume_spike_threshold: float = 300.0  # Percentage threshold

    # Whale Detection
    whale_sol_threshold: float = 10.0  # SOL amount threshold
    whale_first_minutes: int = 5  # First N minutes of token launch

    @property
    def sync_database_url(self) -> str:
        """Convert async URL to sync URL for migrations."""
        return self.database_url.replace("+asyncpg", "")


settings = Settings()

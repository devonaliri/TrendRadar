"""Configuration management for TrendRadar.

Loads and validates settings from environment variables and config files.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional

from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


@dataclass
class DatabaseConfig:
    """Database connection settings."""
    host: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("DB_PORT", "5432")))
    name: str = field(default_factory=lambda: os.getenv("DB_NAME", "trendradar"))
    user: str = field(default_factory=lambda: os.getenv("DB_USER", "postgres"))
    password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))

    @property
    def url(self) -> str:
        """Construct a SQLAlchemy-compatible connection URL."""
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )


@dataclass
class RedisConfig:
    """Redis connection settings used for caching and task queues."""
    host: str = field(default_factory=lambda: os.getenv("REDIS_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("REDIS_PORT", "6379")))
    db: int = field(default_factory=lambda: int(os.getenv("REDIS_DB", "0")))
    password: Optional[str] = field(
        default_factory=lambda: os.getenv("REDIS_PASSWORD") or None
    )

    @property
    def url(self) -> str:
        """Construct a Redis connection URL."""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


@dataclass
class CrawlerConfig:
    """Settings that control crawler behaviour."""
    # Comma-separated list of target sources, e.g. "github,hackernews,reddit"
    sources: List[str] = field(
        default_factory=lambda: [
            s.strip()
            for s in os.getenv("CRAWLER_SOURCES", "github,hackernews").split(",")
            if s.strip()
        ]
    )
    # Maximum concurrent requests per source
    concurrency: int = field(
        default_factory=lambda: int(os.getenv("CRAWLER_CONCURRENCY", "5"))
    )
    # Seconds to wait between retries on failure
    retry_delay: float = field(
        default_factory=lambda: float(os.getenv("CRAWLER_RETRY_DELAY", "2.0"))
    )
    # Maximum number of retries per request
    max_retries: int = field(
        default_factory=lambda: int(os.getenv("CRAWLER_MAX_RETRIES", "3"))
    )
    # Request timeout in seconds
    request_timeout: float = field(
        default_factory=lambda: float(os.getenv("CRAWLER_REQUEST_TIMEOUT", "10.0"))
    )
    # GitHub personal access token (optional, raises rate limit)
    github_token: Optional[str] = field(
        default_factory=lambda: os.getenv("GITHUB_TOKEN") or None
    )


@dataclass
class AppConfig:
    """Top-level application configuration."""
    debug: bool = field(
        default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true"
    )
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper()
    )
    secret_key: str = field(
        default_factory=lambda: os.getenv("SECRET_KEY", "change-me-in-production")
    )
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    crawler: CrawlerConfig = field(default_factory=CrawlerConfig)

    def validate(self) -> None:
        """Raise ValueError for obviously invalid configuration values."""
        if not self.secret_key or self.secret_key == "change-me-in-production":
            if not self.debug:
                raise ValueError(
                    "SECRET_KEY must be set to a secure value in production."
                )
        if self.crawler.concurrency < 1:
            raise ValueError("CRAWLER_CONCURRENCY must be at least 1.")
        if not self.crawler.sources:
            raise ValueError("CRAWLER_SOURCES must contain at least one source.")


# Module-level singleton — import this everywhere
config = AppConfig()

"""
Application Configuration

Enterprise-grade configuration management with:
- Environment-based settings (development, staging, production)
- Separation of secrets from code
- Validation and type safety
- Safe defaults for demos
"""

import os
from enum import Enum
from functools import lru_cache
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# -----------------------------------------------------------------------------
# Environment Definitions
# -----------------------------------------------------------------------------

class Environment(str, Enum):
    """Deployment environment types."""
    
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """Logging level options."""
    
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# -----------------------------------------------------------------------------
# Settings Classes
# -----------------------------------------------------------------------------

class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="DB_",
        env_file=".env",
        extra="ignore",
    )
    
    # For demo: in-memory storage by default
    USE_MEMORY_STORE: bool = True
    
    # Database connection (for future use)
    HOST: str = "localhost"
    PORT: int = 5432
    NAME: str = "call_center"
    USER: str = "postgres"
    PASSWORD: str = ""  # Must be set via environment
    
    # Connection pool
    POOL_SIZE: int = 5
    MAX_OVERFLOW: int = 10
    
    @property
    def connection_url(self) -> str:
        """Build database connection URL."""
        if self.USE_MEMORY_STORE:
            return "memory://"
        return f"postgresql://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"


class RedisSettings(BaseSettings):
    """Redis configuration settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        env_file=".env",
        extra="ignore",
    )
    
    # For demo: disabled by default
    ENABLED: bool = False
    
    HOST: str = "localhost"
    PORT: int = 6379
    PASSWORD: str = ""
    DB: int = 0
    
    # Connection settings
    SOCKET_TIMEOUT: int = 5
    RETRY_ON_TIMEOUT: bool = True
    
    @property
    def connection_url(self) -> str:
        """Build Redis connection URL."""
        auth = f":{self.PASSWORD}@" if self.PASSWORD else ""
        return f"redis://{auth}{self.HOST}:{self.PORT}/{self.DB}"


class LLMSettings(BaseSettings):
    """LLM provider configuration settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        env_file=".env",
        extra="ignore",
    )
    
    # Provider selection
    PROVIDER: str = "openai"  # openai, anthropic, azure, mock
    
    # For demo: can run without LLM
    ENABLED: bool = True
    USE_MOCK: bool = False  # Use mock LLM for demos without API key
    
    # Rate limiting
    MAX_REQUESTS_PER_MINUTE: int = 60
    MAX_TOKENS_PER_REQUEST: int = 1000
    
    # Timeouts
    REQUEST_TIMEOUT_SECONDS: float = 30.0
    
    # Retry configuration
    MAX_RETRIES: int = 3
    RETRY_DELAY_SECONDS: float = 1.0


class OpenAISettings(BaseSettings):
    """OpenAI-specific settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="OPENAI_",
        env_file=".env",
        extra="ignore",
    )
    
    # API configuration (secrets - never hardcode)
    API_KEY: str = ""
    ORGANIZATION: Optional[str] = None
    
    # Model defaults
    DEFAULT_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Custom endpoint (for Azure OpenAI or proxies)
    BASE_URL: Optional[str] = None
    API_VERSION: Optional[str] = None  # For Azure
    
    @property
    def is_configured(self) -> bool:
        """Check if OpenAI is properly configured."""
        return bool(self.API_KEY)


class AnthropicSettings(BaseSettings):
    """Anthropic-specific settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="ANTHROPIC_",
        env_file=".env",
        extra="ignore",
    )
    
    API_KEY: str = ""
    DEFAULT_MODEL: str = "claude-3-haiku-20240307"
    
    @property
    def is_configured(self) -> bool:
        """Check if Anthropic is properly configured."""
        return bool(self.API_KEY)


class SecuritySettings(BaseSettings):
    """Security configuration settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="SECURITY_",
        env_file=".env",
        extra="ignore",
    )
    
    # API keys (for protecting the API)
    API_KEY_ENABLED: bool = False
    API_KEY_HEADER: str = "X-API-Key"
    API_KEYS: List[str] = Field(default_factory=list)
    
    # CORS settings
    CORS_ENABLED: bool = True
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = Field(default_factory=lambda: ["*"])
    CORS_ALLOW_HEADERS: List[str] = Field(default_factory=lambda: ["*"])
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    
    # JWT settings (for future auth)
    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 60
    
    @field_validator("API_KEYS", mode="before")
    @classmethod
    def parse_api_keys(cls, v):
        """Parse comma-separated API keys from env."""
        if isinstance(v, str):
            return [k.strip() for k in v.split(",") if k.strip()]
        return v or []


class TelemetrySettings(BaseSettings):
    """Telemetry and observability settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="TELEMETRY_",
        env_file=".env",
        extra="ignore",
    )
    
    # For demo: basic logging only
    ENABLED: bool = True
    
    # Structured logging
    LOG_FORMAT: str = "json"  # json, text
    LOG_LEVEL: LogLevel = LogLevel.INFO
    
    # Metrics (for future Prometheus/StatsD)
    METRICS_ENABLED: bool = False
    METRICS_PORT: int = 9090
    
    # Tracing (for future OpenTelemetry)
    TRACING_ENABLED: bool = False
    TRACING_SAMPLE_RATE: float = 0.1


class AgentSettings(BaseSettings):
    """AI Agent behavior settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="AGENT_",
        env_file=".env",
        extra="ignore",
    )
    
    # Confidence thresholds
    AUTONOMOUS_THRESHOLD: float = 0.7  # Above this: handle autonomously
    SUPERVISION_THRESHOLD: float = 0.5  # Between this and autonomous: needs review
    ESCALATION_THRESHOLD: float = 0.4  # Below this: escalate
    
    # Response generation
    MAX_RESPONSE_LENGTH: int = 1000
    DEFAULT_TEMPERATURE: float = 0.3
    
    # Escalation limits
    MAX_RETRIES_BEFORE_ESCALATION: int = 2
    MAX_TURNS_PER_INTERACTION: int = 50
    
    # Timeouts
    PROCESSING_TIMEOUT_SECONDS: float = 30.0


class AuditSettings(BaseSettings):
    """Audit and compliance settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="AUDIT_",
        env_file=".env",
        extra="ignore",
    )
    
    # Audit logging
    ENABLED: bool = True
    LOG_DECISIONS: bool = True
    LOG_CONFIDENCE: bool = True
    LOG_ESCALATIONS: bool = True
    
    # Retention
    MAX_INTERACTIONS: int = 10000
    MAX_RECORDS_PER_INTERACTION: int = 100
    
    # Data privacy
    HASH_CUSTOMER_IDS: bool = True
    REDACT_PII: bool = True


# -----------------------------------------------------------------------------
# Main Settings Class
# -----------------------------------------------------------------------------

class Settings(BaseSettings):
    """
    Main application settings.
    
    Loads configuration from:
    1. Environment variables (highest priority)
    2. .env file
    3. Default values
    
    Usage:
        from app.core.config import settings
        
        if settings.DEBUG:
            print("Running in debug mode")
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    
    # Application identity
    APP_NAME: str = "AI Call Center"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "AI-Powered Digital Call Center"
    
    # Environment
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False
    
    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    
    # API settings
    API_PREFIX: str = "/api"
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS (for development)
    ALLOWED_ORIGINS: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"]
    )
    
    # Documentation
    DOCS_ENABLED: bool = True
    
    # Nested settings (loaded separately)
    # Access via get_* functions for lazy loading
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        """Parse comma-separated origins from env."""
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v or []
    
    @model_validator(mode="after")
    def configure_for_environment(self):
        """Apply environment-specific configuration."""
        if self.ENVIRONMENT == Environment.PRODUCTION:
            # Production defaults
            if not self.DEBUG:
                self.DOCS_ENABLED = False
        elif self.ENVIRONMENT == Environment.DEVELOPMENT:
            # Development defaults
            self.DEBUG = True
            self.DOCS_ENABLED = True
        
        return self
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == Environment.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT == Environment.DEVELOPMENT
    
    @property
    def is_testing(self) -> bool:
        """Check if running in test mode."""
        return self.ENVIRONMENT == Environment.TESTING


# -----------------------------------------------------------------------------
# Settings Accessors (Lazy Loading)
# -----------------------------------------------------------------------------

@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


@lru_cache()
def get_database_settings() -> DatabaseSettings:
    """Get cached database settings."""
    return DatabaseSettings()


@lru_cache()
def get_redis_settings() -> RedisSettings:
    """Get cached Redis settings."""
    return RedisSettings()


@lru_cache()
def get_llm_settings() -> LLMSettings:
    """Get cached LLM settings."""
    return LLMSettings()


@lru_cache()
def get_openai_settings() -> OpenAISettings:
    """Get cached OpenAI settings."""
    return OpenAISettings()


@lru_cache()
def get_anthropic_settings() -> AnthropicSettings:
    """Get cached Anthropic settings."""
    return AnthropicSettings()


@lru_cache()
def get_security_settings() -> SecuritySettings:
    """Get cached security settings."""
    return SecuritySettings()


@lru_cache()
def get_telemetry_settings() -> TelemetrySettings:
    """Get cached telemetry settings."""
    return TelemetrySettings()


@lru_cache()
def get_agent_settings() -> AgentSettings:
    """Get cached agent settings."""
    return AgentSettings()


@lru_cache()
def get_audit_settings() -> AuditSettings:
    """Get cached audit settings."""
    return AuditSettings()


def clear_settings_cache() -> None:
    """Clear all cached settings (useful for testing)."""
    get_settings.cache_clear()
    get_database_settings.cache_clear()
    get_redis_settings.cache_clear()
    get_llm_settings.cache_clear()
    get_openai_settings.cache_clear()
    get_anthropic_settings.cache_clear()
    get_security_settings.cache_clear()
    get_telemetry_settings.cache_clear()
    get_agent_settings.cache_clear()
    get_audit_settings.cache_clear()


# -----------------------------------------------------------------------------
# Convenience Exports
# -----------------------------------------------------------------------------

# Primary settings instance (for backward compatibility)
settings = get_settings()


def get_all_settings() -> Dict[str, Any]:
    """
    Get all settings as a dictionary (for debugging).
    
    WARNING: May contain secrets - never log in production.
    """
    return {
        "app": settings.model_dump(),
        "database": get_database_settings().model_dump(),
        "redis": get_redis_settings().model_dump(),
        "llm": get_llm_settings().model_dump(),
        "openai": {
            k: v for k, v in get_openai_settings().model_dump().items()
            if k != "API_KEY"  # Never expose
        },
        "security": {
            k: v for k, v in get_security_settings().model_dump().items()
            if k not in ("API_KEYS", "JWT_SECRET")  # Never expose
        },
        "telemetry": get_telemetry_settings().model_dump(),
        "agent": get_agent_settings().model_dump(),
        "audit": get_audit_settings().model_dump(),
    }


def validate_production_settings() -> List[str]:
    """
    Validate that all required production settings are configured.
    
    Returns a list of missing or invalid settings.
    """
    issues = []
    
    # Check environment
    if settings.ENVIRONMENT != Environment.PRODUCTION:
        issues.append("ENVIRONMENT is not set to 'production'")
    
    if settings.DEBUG:
        issues.append("DEBUG should be False in production")
    
    # Check CORS
    if "*" in settings.ALLOWED_ORIGINS:
        issues.append("ALLOWED_ORIGINS should not contain '*' in production")
    
    # Check security
    security = get_security_settings()
    if not security.JWT_SECRET:
        issues.append("SECURITY_JWT_SECRET is not set")
    
    # Check LLM
    llm = get_llm_settings()
    if llm.ENABLED and not llm.USE_MOCK:
        openai = get_openai_settings()
        anthropic = get_anthropic_settings()
        
        if llm.PROVIDER == "openai" and not openai.is_configured:
            issues.append("OPENAI_API_KEY is not set")
        elif llm.PROVIDER == "anthropic" and not anthropic.is_configured:
            issues.append("ANTHROPIC_API_KEY is not set")
    
    return issues

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database — read-only TenantDB service account
    db_connection_string: str

    # LLM API
    anthropic_api_key: str

    # LangSmith tracing
    langchain_api_key: str = ""
    langchain_tracing_v2: str = "true"
    langchain_project: str = "casci-scenario-planning"

    # Model routing — pinned to exact IDs, never aliases
    llm_scenario_generator: str = "claude-sonnet-4-6"
    llm_demand_decomp: str = "claude-sonnet-4-6"
    llm_narration: str = "claude-haiku-4-5-20251001"  # supply + financial narration

    # Guardrail thresholds
    confidence_low_threshold: float = 0.4
    confidence_critical_threshold: float = 0.1
    max_lift_assumption: float = 6.0
    min_lift_assumption: float = 1.0
    min_scenario_lift_spread: float = 0.5  # aggressive - conservative must be >= this

    # Operational
    agent_timeout_seconds: int = 120
    llm_max_retries: int = 3


settings = Settings()

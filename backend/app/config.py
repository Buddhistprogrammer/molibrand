"""应用配置：从环境变量 / .env 读取。参考 .env.example。"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ---- 百炼 DashScope ----
    dashscope_api_key: str = ""
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_chat_model: str = "qwen3.7-plus"
    llm_flash_model: str = "qwen3.6-flash"
    llm_omni_model: str = "qwen3.5-omni-plus"
    embedding_model: str = "text-embedding-v4"
    embedding_dim: int = 1024
    rerank_model: str = "qwen3-rerank"
    asr_model: str = "fun-asr-realtime"
    tts_model: str = "cosyvoice-v3.5-plus"

    # ---- MySQL（业务数据） ----
    mysql_host: str = "mysql"
    mysql_port: int = 3306
    mysql_db: str = "brand_consult"
    mysql_user: str = "brand_app"
    mysql_password: str = "brand_app_pwd"

    # ---- PostgreSQL + pgvector（向量数据） ----
    pg_host: str = "postgres"
    pg_port: int = 5432
    pg_db: str = "brand_consult"
    pg_user: str = "brand_app"
    pg_password: str = "brand_app_pwd"

    # ---- Redis ----
    redis_url: str = "redis://redis:6379/0"

    # ---- OSS / STS ----
    oss_endpoint: str = ""
    oss_region: str = "cn-hangzhou"
    oss_bucket: str = ""
    oss_access_key_id: str = ""
    oss_access_key_secret: str = ""
    sts_role_arn: str = ""
    sts_duration_seconds: int = 900

    # ---- 应用 ----
    app_env: str = "development"
    jwt_secret: str = "change-me"
    jwt_expire_minutes: int = 1440
    cors_origins: str = "http://localhost:5173,http://localhost"
    daily_llm_call_limit: int = 2000

    @property
    def mysql_dsn(self) -> str:
        return (
            f"mysql+asyncmy://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}?charset=utf8mb4"
        )

    @property
    def pg_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.pg_user}:{self.pg_password}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_db}"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def llm_enabled(self) -> bool:
        """未配置 API Key 时降级为 mock，方便本地起服务。"""
        return bool(self.dashscope_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

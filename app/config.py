from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_interview"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/ai_interview"
    redis_url: str = "redis://localhost:6379/0"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    dashscope_api_key: str = ""
    dashscope_embedding_model: str = "text-embedding-v2"
    upload_dir: str = "./uploads"
    secret_key: str = "dev-secret"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

settings = Settings()

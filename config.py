from dotenv import load_dotenv
load_dotenv()

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str | None = None
    kimi_api_key: str | None = None
    use_kimi_api: bool = False

    # dirs
    upload_dir: str = "data/uploads"
    processed_dir: str = "data/processed"

    # ✅ embeddings config
    kimi_embed_model: str = "text-embedding-v1"
    openai_embed_model: str = "text-embedding-3-large"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

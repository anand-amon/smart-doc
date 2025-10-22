from dotenv import load_dotenv
load_dotenv()  # 👈 this loads your .env automatically

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str | None = None
    kimi_api_key: str | None = None
    use_kimi_api: bool = False   # 👈 add this line
    upload_dir: str = "data/uploads"
    processed_dir: str = "data/processed"

    class Config:
        env_file = ".env"
        extra = "ignore"   # optional safety, ignores unknown vars

settings = Settings()

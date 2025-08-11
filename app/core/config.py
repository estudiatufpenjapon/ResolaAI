from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Configuration using python-dotenv instead of pydantic-settings"""

    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        self.secret_key = os.getenv("SECRET_KEY")
        self.algorithm = os.getenv("ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.api_v1_str = "/api/v1"
        self.project_name = "Mario Audit Log API"


settings = Settings()
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    # Database
    DATABASE_URL = "sqlite:///./backtest.db"
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "backtest_db")
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # Development settings
    DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "true").lower() == "true"
    DEV_USER_ID = int(os.getenv("DEV_USER_ID", "1"))  # Default dev user ID
    
    # CORS
    ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:3001"]
    
    # API
    API_TITLE = "Backtest API"
    API_VERSION = "1.0.0"

settings = Settings()

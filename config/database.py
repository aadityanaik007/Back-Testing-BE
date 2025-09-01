from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pymongo import MongoClient
from .settings import settings

# SQLAlchemy setup (for users and backtest results)
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# MongoDB setup (for strategies)
mongo_client = MongoClient(settings.MONGODB_URL)
mongo_db = mongo_client[settings.MONGODB_DATABASE]
strategies_collection = mongo_db.strategies

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency to get MongoDB
def get_mongo_db():
    return mongo_db

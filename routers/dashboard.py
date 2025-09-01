from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pymongo.database import Database
from config.database import get_db, get_mongo_db
from schemas.backtest import DashboardStats
from services.backtest_service import BacktestService
from services.strategy_service import StrategyService
from utils.dependencies import get_current_user
from models.user import User

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

def get_backtest_service(mongo_db: Database = Depends(get_mongo_db)) -> BacktestService:
    strategy_service = StrategyService(mongo_db)
    return BacktestService(strategy_service)

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    backtest_service: BacktestService = Depends(get_backtest_service)
):
    """Get dashboard statistics for the current user"""
    return backtest_service.get_dashboard_stats(db, current_user)

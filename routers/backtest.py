from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pymongo.database import Database
from typing import List
from config.database import get_db, get_mongo_db
from schemas.backtest import BacktestRequest, BacktestExecuteRequest, BacktestResultResponse
from services.backtest_service import BacktestService
from services.strategy_service import StrategyService
from utils.dependencies import get_current_user
from models.user import User
import json

router = APIRouter(prefix="/api/backtest", tags=["Backtest"])

def get_backtest_service(mongo_db: Database = Depends(get_mongo_db)) -> BacktestService:
    strategy_service = StrategyService(mongo_db)
    return BacktestService(strategy_service)

def get_strategy_service(mongo_db: Database = Depends(get_mongo_db)) -> StrategyService:
    return StrategyService(mongo_db)

@router.get("/results", response_model=List[BacktestResultResponse])
async def get_backtest_results(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    backtest_service: BacktestService = Depends(get_backtest_service)
):
    """Get all backtest results for the current user"""
    return backtest_service.get_backtest_results(db, current_user)

@router.get("/results/{result_id}")
async def get_backtest_result_detail(
    result_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    backtest_service: BacktestService = Depends(get_backtest_service)
):
    """Get detailed backtest result by ID"""
    result = backtest_service.get_backtest_result_detail(db, result_id, current_user)
    if not result:
        raise HTTPException(status_code=404, detail="Backtest result not found")
    
    return {
        "id": result.id,
        "strategy_id": result.strategy_id,
        "total_trades": result.total_trades,
        "winning_trades": result.winning_trades,
        "losing_trades": result.losing_trades,
        "win_rate": result.win_rate,
        "total_pnl": result.total_pnl,
        "max_drawdown": result.max_drawdown,
        "sharpe_ratio": result.sharpe_ratio,
        "results_data": json.loads(result.results_data) if result.results_data else None,
        "created_at": result.created_at
    }

@router.post("/execute")
async def execute_backtest(
    backtest_request: BacktestExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a backtest with given strategy and parameters (placeholder)"""
    # For now, just return a placeholder response
    # This will be implemented when backtest_service is ready
    return {
        "success": False,
        "message": "Backtest execution not yet implemented",
        "strategy_name": backtest_request.name
    }

@router.post("/run/{strategy_id}")
async def run_backtest_for_strategy(
    strategy_id: str,
    backtest_request: BacktestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Run backtest for an existing strategy (placeholder)"""
    # Get the strategy to validate it exists
    strategy = strategy_service.get_strategy(strategy_id, current_user)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    # For now, just return a placeholder response
    return {
        "success": False,
        "message": "Backtest execution not yet implemented",
        "strategy_id": strategy_id,
        "strategy_name": strategy.name
    }

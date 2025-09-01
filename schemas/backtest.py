from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class BacktestRequest(BaseModel):
    strategy_id: str  # MongoDB ObjectId as string
    start_date: str  # YYYY-MM-DD format
    end_date: str    # YYYY-MM-DD format

class BacktestExecuteRequest(BaseModel):
    name: str
    description: Optional[str] = None
    config: dict
    start_date: str  # YYYY-MM-DD format
    end_date: str    # YYYY-MM-DD format

class BacktestResultResponse(BaseModel):
    id: int
    strategy_id: str  # MongoDB ObjectId as string
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    max_drawdown: float
    sharpe_ratio: float
    created_at: datetime

class DashboardStats(BaseModel):
    total_strategies: int
    total_backtests: int
    avg_win_rate: float
    total_pnl: float
    best_strategy: Optional[dict]
    recent_results: List[dict]

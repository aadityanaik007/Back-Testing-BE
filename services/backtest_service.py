from sqlalchemy.orm import Session
from typing import List
from models.backtest import BacktestResult
from models.user import User
from schemas.backtest import DashboardStats
from services.strategy_service import StrategyService

class BacktestService:
    
    def __init__(self, strategy_service: StrategyService):
        self.strategy_service = strategy_service
    
    def get_dashboard_stats(self, db: Session, user: User) -> DashboardStats:
        """Get dashboard statistics for a user"""
        # Get total strategies from MongoDB
        total_strategies = self.strategy_service.count_user_strategies(user)
        
        # Get backtest results from SQLite
        backtest_results = db.query(BacktestResult).filter(BacktestResult.user_id == user.id).all()
        total_backtests = len(backtest_results)
        
        # Calculate statistics
        if backtest_results:
            avg_win_rate = sum(result.win_rate for result in backtest_results) / len(backtest_results)
            total_pnl = sum(result.total_pnl for result in backtest_results)
            
            # Find best strategy
            best_result = max(backtest_results, key=lambda x: x.total_pnl)
            best_strategy_data = self.strategy_service.get_strategy(best_result.strategy_id, user)
            best_strategy = {
                "name": best_strategy_data.name,
                "pnl": best_result.total_pnl,
                "win_rate": best_result.win_rate
            } if best_strategy_data else None
            
            # Recent results
            recent_results = []
            for result in sorted(backtest_results, key=lambda x: x.created_at, reverse=True)[:5]:
                strategy_data = self.strategy_service.get_strategy(result.strategy_id, user)
                recent_results.append({
                    "id": result.id,
                    "strategy_name": strategy_data.name if strategy_data else "Unknown Strategy",
                    "total_pnl": result.total_pnl,
                    "win_rate": result.win_rate,
                    "created_at": result.created_at
                })
        else:
            avg_win_rate = 0.0
            total_pnl = 0.0
            best_strategy = None
            recent_results = []
        
        return DashboardStats(
            total_strategies=total_strategies,
            total_backtests=total_backtests,
            avg_win_rate=avg_win_rate,
            total_pnl=total_pnl,
            best_strategy=best_strategy,
            recent_results=recent_results
        )
    
    def get_backtest_results(self, db: Session, user: User) -> List[BacktestResult]:
        """Get all backtest results for a user"""
        return db.query(BacktestResult).filter(BacktestResult.user_id == user.id).all()
    
    def get_backtest_result_detail(self, db: Session, result_id: int, user: User) -> BacktestResult:
        """Get detailed backtest result by ID"""
        return db.query(BacktestResult).filter(
            BacktestResult.id == result_id, 
            BacktestResult.user_id == user.id
        ).first()

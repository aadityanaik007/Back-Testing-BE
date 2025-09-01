from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime
from config.database import Base

class BacktestResult(Base):
    __tablename__ = "backtest_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    strategy_id = Column(String, nullable=False)  # MongoDB ObjectId as string
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)
    win_rate = Column(Float)
    total_pnl = Column(Float)
    max_drawdown = Column(Float)
    sharpe_ratio = Column(Float)
    results_data = Column(Text)  # JSON string of detailed results
    created_at = Column(DateTime, default=datetime.utcnow)

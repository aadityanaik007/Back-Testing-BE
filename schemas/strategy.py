from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class FilterCondition(BaseModel):
    indicatorA: str
    valueA: str
    sign: str
    indicatorB: str
    valueB: str

class LegConfig(BaseModel):
    legSegmentName: Optional[str] = None
    expiry: Optional[str] = None
    segment: Optional[str] = None
    optionType: Optional[str] = None
    position: Optional[str] = None
    strike: Optional[str] = None
    strikeSelectionParameter: Optional[str] = None
    lotSize: Optional[float] = 0
    targetProfit: Optional[float] = 0
    stopLoss: Optional[float] = 0

class StrategyConfig(BaseModel):
    # Legacy fields for backward compatibility
    timeFrame: Optional[int] = None
    filters: List[FilterCondition] = []
    
    # New comprehensive fields
    index: Optional[str] = None
    expiry: Optional[str] = None
    strategyDuration: Optional[str] = None
    entryTime: Optional[str] = None
    exitTime: Optional[str] = None
    noReentryAfter: Optional[str] = None
    noExitAfter: Optional[str] = None
    overlapEntryAllowed: Optional[bool] = False
    legwiseExit: Optional[bool] = False
    legwiseSquareoff: Optional[str] = None
    totalStopLoss: Optional[float] = 0
    totalTarget: Optional[float] = 0
    timeExit: Optional[int] = 0
    trailingSL: Optional[float] = 0
    technicalSignal: Optional[str] = None
    legs: List[LegConfig] = []

class StrategyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    config: StrategyConfig

class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[StrategyConfig] = None

class StrategyResponse(BaseModel):
    id: str  # MongoDB ObjectId as string
    name: str
    description: Optional[str]
    config: StrategyConfig
    created_at: datetime
    updated_at: datetime
    is_active: bool
    backtest_completed: bool = False

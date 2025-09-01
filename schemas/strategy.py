from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class FilterCondition(BaseModel):
    indicatorA: str
    valueA: str
    sign: str
    indicatorB: str
    valueB: str

class StrategyConfig(BaseModel):
    timeFrame: int
    filters: List[FilterCondition]

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

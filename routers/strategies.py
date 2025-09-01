from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database
from typing import List
from config.database import get_mongo_db
from schemas.strategy import StrategyCreate, StrategyUpdate, StrategyResponse
from services.strategy_service import StrategyService
from utils.dependencies import get_current_user
from models.user import User

router = APIRouter(prefix="/api/strategies", tags=["Strategies"])

def get_strategy_service(mongo_db: Database = Depends(get_mongo_db)) -> StrategyService:
    return StrategyService(mongo_db)

@router.post("", response_model=StrategyResponse)
async def create_strategy(
    strategy: StrategyCreate,
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Create a new strategy"""
    return strategy_service.create_strategy(strategy, current_user)

@router.get("", response_model=List[StrategyResponse])
async def get_strategies(
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Get all active strategies for the current user"""
    return strategy_service.get_strategies(current_user)

@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Get a specific strategy by ID"""
    strategy = strategy_service.get_strategy(strategy_id, current_user)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy

@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: str,
    strategy_update: StrategyUpdate,
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Update an existing strategy"""
    strategy = strategy_service.update_strategy(strategy_id, strategy_update, current_user)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy

@router.delete("/{strategy_id}")
async def delete_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Delete a strategy (soft delete)"""
    success = strategy_service.delete_strategy(strategy_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return {"message": "Strategy deleted successfully"}

@router.post("/{strategy_id}/duplicate", response_model=StrategyResponse)
async def duplicate_strategy(
    strategy_id: str,
    new_name: str,
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Duplicate an existing strategy with a new name"""
    strategy = strategy_service.duplicate_strategy(strategy_id, new_name, current_user)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy

@router.get("/templates")
async def get_strategy_templates():
    """Get predefined strategy templates"""
    templates = [
        {
            "name": "Bull Credit Spread",
            "description": "Options strategy that profits from bullish price movements with limited risk",
            "config": {
                "timeFrame": 15,
                "filters": [
                    {
                        "indicatorA": "RSI(14)",
                        "valueA": "50",
                        "sign": "Greater than",
                        "indicatorB": "Price",
                        "valueB": "100"
                    }
                ]
            }
        },
        {
            "name": "Conservative Bull Spread",
            "description": "Lower risk bull credit spread with tighter stop losses",
            "config": {
                "timeFrame": 30,
                "filters": [
                    {
                        "indicatorA": "RSI(14)",
                        "valueA": "45",
                        "sign": "Greater than",
                        "indicatorB": "SMA",
                        "valueB": "50"
                    }
                ]
            }
        },
        {
            "name": "Aggressive Bull Spread",
            "description": "Higher risk bull credit spread with wider spreads",
            "config": {
                "timeFrame": 60,
                "filters": [
                    {
                        "indicatorA": "RSI(14)",
                        "valueA": "55",
                        "sign": "Greater than",
                        "indicatorB": "EMA",
                        "valueB": "21"
                    }
                ]
            }
        }
    ]
    
    return {"templates": templates}

@router.post("/from-template", response_model=StrategyResponse)
async def create_strategy_from_template(
    template_name: str,
    strategy_name: str,
    current_user: User = Depends(get_current_user),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Create a new strategy from a predefined template"""
    # Get templates
    templates_response = await get_strategy_templates()
    templates = templates_response["templates"]
    template = next((t for t in templates if t['name'] == template_name), None)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Create strategy from template
    from schemas.strategy import StrategyConfig, FilterCondition
    
    filters = [FilterCondition(**filter_data) for filter_data in template['config']['filters']]
    config = StrategyConfig(timeFrame=template['config']['timeFrame'], filters=filters)
    
    strategy_create = StrategyCreate(
        name=strategy_name,
        description=template['description'],
        config=config
    )
    
    return strategy_service.create_strategy(strategy_create, current_user)

from pymongo.database import Database
from bson import ObjectId
from datetime import datetime
from typing import List, Optional
from schemas.strategy import StrategyCreate, StrategyUpdate, StrategyResponse
from models.user import User

class StrategyService:
    
    def __init__(self, mongo_db: Database):
        self.collection = mongo_db.strategies
    
    def create_strategy(self, strategy: StrategyCreate, user: User) -> StrategyResponse:
        """Create a new strategy in MongoDB"""
        strategy_doc = {
            "user_id": user.id,
            "name": strategy.name,
            "description": strategy.description,
            "config": strategy.config.dict(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
        
        result = self.collection.insert_one(strategy_doc)
        strategy_doc["_id"] = result.inserted_id
        
        return self._doc_to_response(strategy_doc)
    
    def get_strategies(self, user: User) -> List[StrategyResponse]:
        """Get all active strategies for a user"""
        strategies = self.collection.find({
            "user_id": user.id,
            "is_active": True
        })
        
        return [self._doc_to_response(doc) for doc in strategies]
    
    def get_strategy(self, strategy_id: str, user: User) -> Optional[StrategyResponse]:
        """Get a specific strategy by ID"""
        strategy = self.collection.find_one({
            "_id": ObjectId(strategy_id),
            "user_id": user.id
        })
        
        if not strategy:
            return None
        
        return self._doc_to_response(strategy)
    
    def update_strategy(self, strategy_id: str, strategy_update: StrategyUpdate, user: User) -> Optional[StrategyResponse]:
        """Update an existing strategy"""
        update_data = {"updated_at": datetime.utcnow()}
        
        if strategy_update.name:
            update_data["name"] = strategy_update.name
        if strategy_update.description is not None:
            update_data["description"] = strategy_update.description
        if strategy_update.config:
            update_data["config"] = strategy_update.config.dict()
        
        result = self.collection.find_one_and_update(
            {"_id": ObjectId(strategy_id), "user_id": user.id},
            {"$set": update_data},
            return_document=True
        )
        
        if not result:
            return None
        
        return self._doc_to_response(result)
    
    def delete_strategy(self, strategy_id: str, user: User) -> bool:
        """Soft delete a strategy"""
        result = self.collection.update_one(
            {"_id": ObjectId(strategy_id), "user_id": user.id},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        
        return result.modified_count > 0
    
    def duplicate_strategy(self, strategy_id: str, new_name: str, user: User) -> Optional[StrategyResponse]:
        """Duplicate an existing strategy"""
        original = self.collection.find_one({
            "_id": ObjectId(strategy_id),
            "user_id": user.id
        })
        
        if not original:
            return None
        
        duplicated_doc = {
            "user_id": user.id,
            "name": new_name,
            "description": f"Copy of {original.get('description', '')}" if original.get('description') else "Copy of strategy",
            "config": original["config"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
        
        result = self.collection.insert_one(duplicated_doc)
        duplicated_doc["_id"] = result.inserted_id
        
        return self._doc_to_response(duplicated_doc)
    
    def count_user_strategies(self, user: User) -> int:
        """Count active strategies for a user"""
        return self.collection.count_documents({
            "user_id": user.id,
            "is_active": True
        })
    
    def _doc_to_response(self, doc: dict) -> StrategyResponse:
        """Convert MongoDB document to StrategyResponse"""
        from schemas.strategy import StrategyConfig, FilterCondition
        
        # Convert config dict back to StrategyConfig
        config_data = doc["config"]
        filters = [FilterCondition(**filter_data) for filter_data in config_data["filters"]]
        config = StrategyConfig(timeFrame=config_data["timeFrame"], filters=filters)
        
        return StrategyResponse(
            id=str(doc["_id"]),
            name=doc["name"],
            description=doc.get("description"),
            config=config,
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
            is_active=doc["is_active"]
        )

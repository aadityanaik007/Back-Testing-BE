from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional, List
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Initialize backtest service

# FastAPI app initialization
app = FastAPI(title="Backtest API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE_URL = "sqlite:///./backtest.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class Strategy(Base):
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    config = Column(Text, nullable=False)  # JSON string of strategy config
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class BacktestResult(Base):
    __tablename__ = "backtest_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    strategy_id = Column(Integer, nullable=False)
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)
    win_rate = Column(Float)
    total_pnl = Column(Float)
    max_drawdown = Column(Float)
    sharpe_ratio = Column(Float)
    results_data = Column(Text)  # JSON string of detailed results
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic models for API
class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime
    is_active: bool

class Token(BaseModel):
    access_token: str
    token_type: str

class StrategyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    config: dict

class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[dict] = None

class StrategyResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    config: dict
    created_at: datetime
    updated_at: datetime
    is_active: bool

class BacktestResultResponse(BaseModel):
    id: int
    strategy_id: int
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

class BacktestRequest(BaseModel):
    strategy_id: int
    start_date: str  # YYYY-MM-DD format
    end_date: str    # YYYY-MM-DD format
    
class BacktestExecuteRequest(BaseModel):
    name: str
    description: Optional[str] = None
    config: dict
    start_date: str  # YYYY-MM-DD format
    end_date: str    # YYYY-MM-DD format

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# API Endpoints

@app.get("/")
async def root():
    return {"message": "Backtest API Server", "version": "1.0.0"}

# ============================================================================
# AUTHENTICATION APIs SECTION
# ============================================================================

@app.post("/api/auth/signup", response_model=UserResponse, tags=["Authentication"])
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        name=user.name,
        email=user.email,
        password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@app.post("/api/auth/login", response_model=Token, tags=["Authentication"])
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return access token"""
    user = db.query(User).filter(User.email == user_credentials.email).first()
    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/auth/logout", tags=["Authentication"])
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user (token invalidation would be handled client-side)"""
    # In a real implementation, you might want to invalidate the token
    # For now, we'll just return a success message
    return {"message": "Successfully logged out"}

@app.get("/api/auth/me", response_model=UserResponse, tags=["Authentication"])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

# ============================================================================
# DASHBOARD APIs SECTION
# ============================================================================

@app.get("/api/dashboard/stats", response_model=DashboardStats, tags=["Dashboard"])
async def get_dashboard_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get dashboard statistics for the current user"""
    # Get user's strategies
    total_strategies = db.query(Strategy).filter(Strategy.user_id == current_user.id).count()
    
    # Get user's backtest results
    backtest_results = db.query(BacktestResult).filter(BacktestResult.user_id == current_user.id).all()
    total_backtests = len(backtest_results)
    
    # Calculate statistics
    if backtest_results:
        avg_win_rate = sum(result.win_rate for result in backtest_results) / len(backtest_results)
        total_pnl = sum(result.total_pnl for result in backtest_results)
        
        # Find best strategy
        best_result = max(backtest_results, key=lambda x: x.total_pnl)
        best_strategy_data = db.query(Strategy).filter(Strategy.id == best_result.strategy_id).first()
        best_strategy = {
            "name": best_strategy_data.name,
            "pnl": best_result.total_pnl,
            "win_rate": best_result.win_rate
        } if best_strategy_data else None
        
        # Recent results
        recent_results = [
            {
                "id": result.id,
                "strategy_name": db.query(Strategy).filter(Strategy.id == result.strategy_id).first().name,
                "total_pnl": result.total_pnl,
                "win_rate": result.win_rate,
                "created_at": result.created_at
            }
            for result in sorted(backtest_results, key=lambda x: x.created_at, reverse=True)[:5]
        ]
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

# ============================================================================
# STRATEGY CRUD APIs SECTION
# ============================================================================

@app.post("/api/strategies", response_model=StrategyResponse, tags=["Strategies"])
async def create_strategy(strategy: StrategyCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new strategy"""
    db_strategy = Strategy(
        user_id=current_user.id,
        name=strategy.name,
        description=strategy.description,
        config=json.dumps(strategy.config)
    )
    db.add(db_strategy)
    db.commit()
    db.refresh(db_strategy)
    
    # Convert config back to dict for response
    response_strategy = StrategyResponse(
        id=db_strategy.id,
        name=db_strategy.name,
        description=db_strategy.description,
        config=json.loads(db_strategy.config),
        created_at=db_strategy.created_at,
        updated_at=db_strategy.updated_at,
        is_active=db_strategy.is_active
    )
    
    return response_strategy

@app.get("/api/strategies", response_model=List[StrategyResponse], tags=["Strategies"])
async def get_strategies(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all active strategies for the current user"""
    strategies = db.query(Strategy).filter(Strategy.user_id == current_user.id, Strategy.is_active == True).all()
    
    response_strategies = []
    for strategy in strategies:
        response_strategies.append(StrategyResponse(
            id=strategy.id,
            name=strategy.name,
            description=strategy.description,
            config=json.loads(strategy.config),
            created_at=strategy.created_at,
            updated_at=strategy.updated_at,
            is_active=strategy.is_active
        ))
    
    return response_strategies

@app.get("/api/strategies/{strategy_id}", response_model=StrategyResponse, tags=["Strategies"])
async def get_strategy(strategy_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get a specific strategy by ID"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    return StrategyResponse(
        id=strategy.id,
        name=strategy.name,
        description=strategy.description,
        config=json.loads(strategy.config),
        created_at=strategy.created_at,
        updated_at=strategy.updated_at,
        is_active=strategy.is_active
    )

@app.put("/api/strategies/{strategy_id}", response_model=StrategyResponse, tags=["Strategies"])
async def update_strategy(strategy_id: int, strategy_update: StrategyUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update an existing strategy"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    if strategy_update.name:
        strategy.name = strategy_update.name
    if strategy_update.description is not None:
        strategy.description = strategy_update.description
    if strategy_update.config:
        strategy.config = json.dumps(strategy_update.config)
    
    strategy.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(strategy)
    
    return StrategyResponse(
        id=strategy.id,
        name=strategy.name,
        description=strategy.description,
        config=json.loads(strategy.config),
        created_at=strategy.created_at,
        updated_at=strategy.updated_at,
        is_active=strategy.is_active
    )

@app.delete("/api/strategies/{strategy_id}", tags=["Strategies"])
async def delete_strategy(strategy_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a strategy (soft delete)"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    # Soft delete
    strategy.is_active = False
    db.commit()
    
    return {"message": "Strategy deleted successfully"}

@app.post("/api/strategies/{strategy_id}/duplicate", response_model=StrategyResponse, tags=["Strategies"])
async def duplicate_strategy(strategy_id: int, new_name: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Duplicate an existing strategy with a new name"""
    original_strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not original_strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    # Create duplicate
    duplicated_strategy = Strategy(
        user_id=current_user.id,
        name=new_name,
        description=f"Copy of {original_strategy.description}" if original_strategy.description else "Copy of strategy",
        config=original_strategy.config
    )
    db.add(duplicated_strategy)
    db.commit()
    db.refresh(duplicated_strategy)
    
    return StrategyResponse(
        id=duplicated_strategy.id,
        name=duplicated_strategy.name,
        description=duplicated_strategy.description,
        config=json.loads(duplicated_strategy.config),
        created_at=duplicated_strategy.created_at,
        updated_at=duplicated_strategy.updated_at,
        is_active=duplicated_strategy.is_active
    )

@app.get("/api/strategies/templates", tags=["Strategies"])
async def get_strategy_templates():
    """Get predefined strategy templates"""
    templates = [
        {
            "name": "Bull Credit Spread",
            "description": "Options strategy that profits from bullish price movements with limited risk",
            "config": {
                'ema9': 9, 
                'ema5': 5, 
                'ema13': 13, 
                'ema21': 21,
                'ema34': 34, 
                'sma40': 40,
                'ema40': 40,
                'sma45': 45,
                'sma50': 50,
                'sma100': 100,
                'sma200': 200,
                'sma300': 300,
                'rsi14': 14,
                'rsi_threshold': 50,
                'body_ratio': 0.6,
                'sell_otm': 0,
                'spread': 200,
                'lot_size': 50,
                'max_profit_per_lot': 100,
                'spot_sl_pct': 0.003,
                'max_hold': 210,
                'min_premium': 30 
            }
        },
        {
            "name": "Conservative Bull Spread",
            "description": "Lower risk bull credit spread with tighter stop losses",
            "config": {
                'ema9': 9, 
                'ema5': 5, 
                'ema13': 13, 
                'ema21': 21,
                'ema34': 34, 
                'sma40': 40,
                'ema40': 40,
                'sma45': 45,
                'sma50': 50,
                'sma100': 100,
                'sma200': 200,
                'sma300': 300,
                'rsi14': 14,
                'rsi_threshold': 45,
                'body_ratio': 0.7,
                'sell_otm': 0,
                'spread': 150,
                'lot_size': 25,
                'max_profit_per_lot': 75,
                'spot_sl_pct': 0.002,
                'max_hold': 180,
                'min_premium': 25 
            }
        },
        {
            "name": "Aggressive Bull Spread",
            "description": "Higher risk bull credit spread with wider spreads",
            "config": {
                'ema9': 9, 
                'ema5': 5, 
                'ema13': 13, 
                'ema21': 21,
                'ema34': 34, 
                'sma40': 40,
                'ema40': 40,
                'sma45': 45,
                'sma50': 50,
                'sma100': 100,
                'sma200': 200,
                'sma300': 300,
                'rsi14': 14,
                'rsi_threshold': 55,
                'body_ratio': 0.5,
                'sell_otm': 100,
                'spread': 300,
                'lot_size': 75,
                'max_profit_per_lot': 150,
                'spot_sl_pct': 0.005,
                'max_hold': 240,
                'min_premium': 40 
            }
        }
    ]
    
    return {"templates": templates}

@app.post("/api/strategies/from-template", response_model=StrategyResponse, tags=["Strategies"])
async def create_strategy_from_template(
    template_name: str,
    strategy_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new strategy from a predefined template"""
    
    # Get templates
    templates_response = await get_strategy_templates()
    templates = templates_response["templates"]
    template = next((t for t in templates if t['name'] == template_name), None)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Create strategy from template
    strategy = Strategy(
        user_id=current_user.id,
        name=strategy_name,
        description=template['description'],
        config=json.dumps(template['config'])
    )
    
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    
    return StrategyResponse(
        id=strategy.id,
        name=strategy.name,
        description=strategy.description,
        config=json.loads(strategy.config),
        created_at=strategy.created_at,
        updated_at=strategy.updated_at,
        is_active=strategy.is_active
    )

# ============================================================================
# BACKTEST RESULTS APIs SECTION
# ============================================================================

@app.get("/api/backtest-results", response_model=List[BacktestResultResponse], tags=["Backtest Results"])
async def get_backtest_results(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all backtest results for the current user"""
    results = db.query(BacktestResult).filter(BacktestResult.user_id == current_user.id).all()
    return results

@app.get("/api/backtest-results/{result_id}", tags=["Backtest Results"])
async def get_backtest_result_detail(result_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get detailed backtest result by ID"""
    result = db.query(BacktestResult).filter(BacktestResult.id == result_id, BacktestResult.user_id == current_user.id).first()
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

# ============================================================================
# BACKTEST EXECUTION APIs SECTION (Placeholder - will be implemented later)
# ============================================================================

@app.post("/api/backtest/execute", tags=["Backtest Execution"])
async def execute_backtest(backtest_request: BacktestExecuteRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Execute a backtest with given strategy and parameters (placeholder)"""
    
    # For now, just return a placeholder response
    # This will be implemented when backtest_service is ready
    return {
        "success": False,
        "message": "Backtest execution not yet implemented",
        "strategy_name": backtest_request.name
    }

@app.post("/api/backtest/run/{strategy_id}", tags=["Backtest Execution"])
async def run_backtest_for_strategy(
    strategy_id: int, 
    backtest_request: BacktestRequest, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Run backtest for an existing strategy (placeholder)"""
    
    # Get the strategy to validate it exists
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    # For now, just return a placeholder response
    return {
        "success": False,
        "message": "Backtest execution not yet implemented",
        "strategy_id": strategy_id,
        "strategy_name": strategy.name
    }

# ============================================================================
# STRATEGY TEMPLATES SECTION  
# ============================================================================

@app.get("/api/strategies/templates", tags=["Strategies"])
async def get_strategy_templates():
    """Get predefined strategy templates"""
    templates = [
        {
            "name": "Bull Credit Spread",
            "description": "Options strategy that profits from bullish price movements with limited risk",
            "config": {
                'ema9': 9, 
                'ema5': 5, 
                'ema13': 13, 
                'ema21': 21,
                'ema34': 34, 
                'sma40': 40,
                'ema40': 40,
                'sma45': 45,
                'sma50': 50,
                'sma100': 100,
                'sma200': 200,
                'sma300': 300,
                'rsi14': 14,
                'rsi_threshold': 50,
                'body_ratio': 0.6,
                'sell_otm': 0,
                'spread': 200,
                'lot_size': 50,
                'max_profit_per_lot': 100,
                'spot_sl_pct': 0.003,
                'max_hold': 210,
                'min_premium': 30 
            }
        },
        {
            "name": "Conservative Bull Spread",
            "description": "Lower risk bull credit spread with tighter stop losses",
            "config": {
                'ema9': 9, 
                'ema5': 5, 
                'ema13': 13, 
                'ema21': 21,
                'ema34': 34, 
                'sma40': 40,
                'ema40': 40,
                'sma45': 45,
                'sma50': 50,
                'sma100': 100,
                'sma200': 200,
                'sma300': 300,
                'rsi14': 14,
                'rsi_threshold': 45,
                'body_ratio': 0.7,
                'sell_otm': 0,
                'spread': 150,
                'lot_size': 25,
                'max_profit_per_lot': 75,
                'spot_sl_pct': 0.002,
                'max_hold': 180,
                'min_premium': 25 
            }
        },
        {
            "name": "Aggressive Bull Spread",
            "description": "Higher risk bull credit spread with wider spreads",
            "config": {
                'ema9': 9, 
                'ema5': 5, 
                'ema13': 13, 
                'ema21': 21,
                'ema34': 34, 
                'sma40': 40,
                'ema40': 40,
                'sma45': 45,
                'sma50': 50,
                'sma100': 100,
                'sma200': 200,
                'sma300': 300,
                'rsi14': 14,
                'rsi_threshold': 55,
                'body_ratio': 0.5,
                'sell_otm': 100,
                'spread': 300,
                'lot_size': 75,
                'max_profit_per_lot': 150,
                'spot_sl_pct': 0.005,
                'max_hold': 240,
                'min_premium': 40 
            }
        }
    ]
    
    return {"templates": templates}

@app.post("/api/strategies/from-template", response_model=StrategyResponse, tags=["Strategies"])
async def create_strategy_from_template(
    template_name: str,
    strategy_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new strategy from a predefined template"""
    
    # Get templates
    templates_response = await get_strategy_templates()
    templates = templates_response["templates"]
    template = next((t for t in templates if t['name'] == template_name), None)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Create strategy from template
    strategy = Strategy(
        user_id=current_user.id,
        name=strategy_name,
        description=template['description'],
        config=json.dumps(template['config'])
    )
    
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    
    return StrategyResponse(
        id=strategy.id,
        name=strategy.name,
        description=strategy.description,
        config=json.loads(strategy.config),
        created_at=strategy.created_at,
        updated_at=strategy.updated_at,
        is_active=strategy.is_active
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

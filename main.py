from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings
from config.database import Base, engine
from routers import auth, strategies, dashboard, backtest, option_data, bull_credit

# Create database tables
Base.metadata.create_all(bind=engine)

# FastAPI app initialization
app = FastAPI(title=settings.API_TITLE, version=settings.API_VERSION)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(strategies.router)
app.include_router(dashboard.router)
app.include_router(backtest.router)
app.include_router(option_data.router)
app.include_router(bull_credit.router)

@app.get("/")
async def root():
    return {"message": "Backtest API Server", "version": settings.API_VERSION}

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker and monitoring"""
    return {
        "status": "healthy",
        "service": "backtest-api",
        "version": settings.API_VERSION
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

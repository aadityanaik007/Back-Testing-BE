from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from config.database import get_db
from config.settings import settings
from schemas.user import UserCreate, UserLogin, UserResponse, Token
from services.auth_service import AuthService
from utils.dependencies import get_current_user
from utils.security import get_password_hash, create_access_token
from models.user import User

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/signup", response_model=UserResponse)
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        db_user = AuthService.create_user(db, user)
        return db_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return access token"""
    try:
        # In development mode, auto-authenticate development users
        if settings.DEVELOPMENT_MODE:
            # Check if this is a development user email
            dev_emails = ["dev@test.com", "user1@test.com", "user2@test.com", "john@test.com", "jane@test.com"]
            if user_credentials.email in dev_emails:
                # Get or create the development user
                user = db.query(User).filter(User.email == user_credentials.email).first()
                if not user:
                    # Create the user automatically in dev mode
                    user = User(
                        name=user_credentials.email.split('@')[0].title(),
                        email=user_credentials.email,
                        password_hash=get_password_hash("devpass123")  # Default dev password
                    )
                    db.add(user)
                    db.commit()
                    db.refresh(user)
                
                # Generate access token without password verification in dev mode
                access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = create_access_token(
                    data={"sub": user.email}, expires_delta=access_token_expires
                )
                return {"access_token": access_token, "token_type": "bearer"}
        
        # Normal authentication flow
        access_token = AuthService.authenticate_user(db, user_credentials)
        return {"access_token": access_token, "token_type": "bearer"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user (token invalidation would be handled client-side)"""
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

# Development endpoints
@router.get("/dev/status")
async def dev_status():
    """Get development mode status"""
    return {
        "development_mode": settings.DEVELOPMENT_MODE,
        "dev_user_id": settings.DEV_USER_ID,
        "message": "Authentication bypassed in development mode" if settings.DEVELOPMENT_MODE else "Production authentication required"
    }

@router.post("/dev/login", response_model=Token)
async def dev_login(email: str = "dev@test.com", db: Session = Depends(get_db)):
    """Development auto-login - get access token for any dev user"""
    if not settings.DEVELOPMENT_MODE:
        raise HTTPException(status_code=403, detail="Only available in development mode")
    
    # Get or create the development user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Create the user automatically in dev mode
        user = User(
            name=email.split('@')[0].title() if email else "Dev User",
            email=email,
            password_hash=get_password_hash("devpass123")  # Default dev password
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Generate access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }

@router.post("/dev/create-test-users")
async def create_test_users(db: Session = Depends(get_db)):
    """Create test users for development"""
    if not settings.DEVELOPMENT_MODE:
        raise HTTPException(status_code=403, detail="Only available in development mode")
    
    test_users = [
        {"name": "Dev User", "email": "dev@test.com", "password": "devpass123"},
        {"name": "Test User 1", "email": "user1@test.com", "password": "password123"},
        {"name": "Test User 2", "email": "user2@test.com", "password": "password123"},
        {"name": "John Doe", "email": "john@test.com", "password": "password123"},
        {"name": "Jane Smith", "email": "jane@test.com", "password": "password123"},
    ]
    
    created_users = []
    for user_data in test_users:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if not existing_user:
            new_user = User(
                name=user_data["name"],
                email=user_data["email"],
                password_hash=get_password_hash(user_data["password"])
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            created_users.append({"id": new_user.id, "name": new_user.name, "email": new_user.email})
        else:
            created_users.append({"id": existing_user.id, "name": existing_user.name, "email": existing_user.email, "existed": True})
    
    return {
        "message": "Test users created/verified",
        "users": created_users,
        "note": "You can use X-Dev-User header with user ID to switch users, or no auth for default dev user (ID: 1)"
    }

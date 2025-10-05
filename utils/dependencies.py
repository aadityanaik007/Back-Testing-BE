from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from config.database import get_db
from config.settings import settings
from models.user import User
from utils.security import verify_token

security = HTTPBearer()

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security), 
    db: Session = Depends(get_db),
    x_dev_user: Optional[str] = Header(None)
) -> User:
    """Get the current authenticated user or dev user in development mode"""
    
    # Development mode bypass
    if settings.DEVELOPMENT_MODE:
        # If X-Dev-User header is provided, use that user ID
        if x_dev_user:
            try:
                dev_user_id = int(x_dev_user)
                user = db.query(User).filter(User.id == dev_user_id).first()
                if user:
                    return user
            except (ValueError, TypeError):
                pass
        
        # If no auth credentials provided in dev mode, use default dev user
        if not credentials:
            user = db.query(User).filter(User.id == settings.DEV_USER_ID).first()
            if user:
                return user
            
            # Create default dev user if doesn't exist
            from utils.security import get_password_hash
            dev_user = User(
                id=settings.DEV_USER_ID,
                name="Dev User",
                email="dev@test.com",
                password_hash=get_password_hash("devpass123")
            )
            db.add(dev_user)
            db.commit()
            db.refresh(dev_user)
            return dev_user
    
    # Production authentication
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials:
        raise credentials_exception
    
    email = verify_token(credentials.credentials)
    if email is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    
    return user

# Optional authentication dependency for endpoints that can work without auth
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)), 
    db: Session = Depends(get_db),
    x_dev_user: Optional[str] = Header(None)
) -> Optional[User]:
    """Get the current user if authenticated, None otherwise"""
    try:
        return await get_current_user(credentials, db, x_dev_user)
    except HTTPException:
        return None
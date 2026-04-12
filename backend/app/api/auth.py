"""
Authentication API routes
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, load_config, save_config
from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.auth import (
    get_password_hash,
    authenticate_user,
    create_access_token,
)
from app.services.audit import log_action

router = APIRouter(prefix="/auth", tags=["Authentication"])


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: str

    class Config:
        from_attributes = True


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user
    """
    # Check if user registration is allowed
    config = load_config()
    if not config.get("allow_user_registration", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User registration is currently disabled"
        )
    
    # Check if username already exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Validate password strength
    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        role="user"
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "message": "User registered successfully",
        "user_id": new_user.id
    }


class RegistrationConfigUpdate(BaseModel):
    allow_registration: bool


class PdfConversionConfigUpdate(BaseModel):
    allow_pdf_conversion: bool


@router.get("/registration-config")
def get_registration_config():
    """
    Get current user registration configuration
    """
    config = load_config()
    return {
        "allow_user_registration": config.get("allow_user_registration", False)
    }


@router.put("/registration-config")
def update_registration_config(
    config_update: RegistrationConfigUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user registration configuration (admin only)
    """
    # Check if user is admin
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Administrators can change this setting"
        )
    
    # Load current config
    config = load_config()
    old_value = config.get("allow_user_registration", False)
    new_value = config_update.allow_registration
    
    # Update config
    config["allow_user_registration"] = new_value
    save_config(config)
    
    # Get client info for audit log
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Log the change to audit log
    log_action(
        db=db,
        user=current_user,
        action="config_change",
        resource_type="registration_config",
        resource_id="allow_user_registration",
        old_value=str(old_value),
        new_value=str(new_value),
        ip_address=client_host,
        user_agent=user_agent
    )
    
    return {
        "message": "Registration configuration updated successfully",
        "allow_user_registration": new_value
    }


@router.get("/pdf-conversion-config")
def get_pdf_conversion_config():
    """
    Get current PDF conversion configuration
    """
    config = load_config()
    return {
        "allow_pdf_conversion": config.get("allow_pdf_conversion", False)
    }


@router.put("/pdf-conversion-config")
def update_pdf_conversion_config(
    config_update: PdfConversionConfigUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update PDF conversion configuration (admin only)
    """
    # Check if user is admin
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Administrators can change this setting"
        )
    
    # Load current config
    config = load_config()
    old_value = config.get("allow_pdf_conversion", False)
    new_value = config_update.allow_pdf_conversion
    
    # Update config
    config["allow_pdf_conversion"] = new_value
    save_config(config)
    
    # Get client info for audit log
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Log the change to audit log
    log_action(
        db=db,
        user=current_user,
        action="config_change",
        resource_type="pdf_conversion_config",
        resource_id="allow_pdf_conversion",
        old_value=str(old_value),
        new_value=str(new_value),
        ip_address=client_host,
        user_agent=user_agent
    )
    
    return {
        "message": "PDF conversion configuration updated successfully",
        "allow_pdf_conversion": new_value
    }


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login and get access token
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user.role
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    }


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None
    )

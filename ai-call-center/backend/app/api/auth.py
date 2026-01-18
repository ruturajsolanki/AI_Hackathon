"""
Authentication API

JWT-based authentication for the AI Call Center.
Supports login, token refresh, and user management.

Security Features:
- Password hashing with bcrypt
- JWT tokens with expiration
- Refresh token rotation
- Secure token storage recommendations
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Check if auth libraries are available
try:
    from jose import jwt, JWTError
    import hashlib
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    logger.warning("Auth libraries not installed. Authentication disabled.")


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# In production, these should come from environment variables
SECRET_KEY = "your-secret-key-change-in-production-use-env-vars"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Simple password hashing (use bcrypt in production with proper setup)
def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt. Use bcrypt in production."""
    salt = SECRET_KEY[:16]
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def verify_password_hash(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == hashed

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# -----------------------------------------------------------------------------
# In-Memory User Store (Replace with MongoDB in production)
# -----------------------------------------------------------------------------

class UserStore:
    """In-memory user store for demo purposes."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._users = {}
            cls._instance._refresh_tokens = {}
            cls._instance._initialize_demo_user()
        return cls._instance
    
    def _initialize_demo_user(self):
        """Create a demo user for testing."""
        if not AUTH_AVAILABLE:
            return
            
        demo_id = str(uuid4())
        self._users["demo@example.com"] = {
            "user_id": demo_id,
            "email": "demo@example.com",
            "hashed_password": hash_password("demo123"),
            "full_name": "Demo User",
            "role": "admin",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    
    def get_user_by_email(self, email: str):
        return self._users.get(email)
    
    def get_user_by_id(self, user_id: str):
        for user in self._users.values():
            if user["user_id"] == user_id:
                return user
        return None
    
    def create_user(self, email: str, password: str, full_name: str, role: str = "user"):
        if email in self._users:
            return None
        
        user_id = str(uuid4())
        self._users[email] = {
            "user_id": user_id,
            "email": email,
            "hashed_password": hash_password(password),
            "full_name": full_name,
            "role": role,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self._users[email]
    
    def store_refresh_token(self, user_id: str, token: str, expires_at: datetime):
        self._refresh_tokens[token] = {
            "user_id": user_id,
            "expires_at": expires_at.isoformat(),
        }
    
    def get_refresh_token(self, token: str):
        return self._refresh_tokens.get(token)
    
    def revoke_refresh_token(self, token: str):
        if token in self._refresh_tokens:
            del self._refresh_tokens[token]


def get_user_store() -> UserStore:
    return UserStore()


# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

class Token(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token expiration in seconds")


class TokenData(BaseModel):
    """Data extracted from JWT token."""
    user_id: str
    email: str
    role: str


class UserCreate(BaseModel):
    """Request to create a new user."""
    email: str = Field(pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=1)


class UserResponse(BaseModel):
    """User information (without password)."""
    user_id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: str


class LoginRequest(BaseModel):
    """Login request."""
    email: str
    password: str


class RefreshRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    if not AUTH_AVAILABLE:
        return False
    return verify_password_hash(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    if not AUTH_AVAILABLE:
        return ""
    
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> tuple[str, datetime]:
    """Create a JWT refresh token."""
    if not AUTH_AVAILABLE:
        return "", datetime.now(timezone.utc)
    
    expires = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    token = jwt.encode(
        {"sub": user_id, "exp": expires, "type": "refresh", "jti": str(uuid4())},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return token, expires


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    if not AUTH_AVAILABLE:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Optional[dict]:
    """Get the current authenticated user from the token."""
    if not token:
        return None
    
    payload = decode_token(token)
    if not payload:
        return None
    
    if payload.get("type") != "access":
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    store = get_user_store()
    user = store.get_user_by_id(user_id)
    
    if not user or not user.get("is_active"):
        return None
    
    return user


async def require_auth(user: dict = Depends(get_current_user)) -> dict:
    """Require authentication for an endpoint."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def require_admin(user: dict = Depends(require_auth)) -> dict:
    """Require admin role for an endpoint."""
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


# -----------------------------------------------------------------------------
# Router
# -----------------------------------------------------------------------------

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate a user and return JWT tokens.
    
    Use the demo credentials for testing:
    - Email: demo@example.com
    - Password: demo123
    """
    if not AUTH_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not available. Install python-jose and passlib.",
        )
    
    store = get_user_store()
    user = store.get_user_by_email(form_data.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": user["user_id"], "email": user["email"], "role": user["role"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    
    refresh_token, refresh_expires = create_refresh_token(user["user_id"])
    store.store_refresh_token(user["user_id"], refresh_token, refresh_expires)
    
    logger.info(f"User logged in: {user['email']}")
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshRequest):
    """
    Refresh an access token using a refresh token.
    
    The old refresh token is invalidated after use (rotation).
    """
    if not AUTH_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not available",
        )
    
    store = get_user_store()
    
    # Validate refresh token
    payload = decode_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    # Check if token is stored (not revoked)
    stored = store.get_refresh_token(request.refresh_token)
    if not stored:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )
    
    user_id = payload.get("sub")
    user = store.get_user_by_id(user_id)
    
    if not user or not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    # Revoke old refresh token (rotation)
    store.revoke_refresh_token(request.refresh_token)
    
    # Create new tokens
    access_token = create_access_token(
        data={"sub": user["user_id"], "email": user["email"], "role": user["role"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    
    new_refresh_token, refresh_expires = create_refresh_token(user["user_id"])
    store.store_refresh_token(user["user_id"], new_refresh_token, refresh_expires)
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
async def logout(
    request: RefreshRequest,
    user: dict = Depends(require_auth),
):
    """
    Logout and revoke refresh token.
    """
    store = get_user_store()
    store.revoke_refresh_token(request.refresh_token)
    
    logger.info(f"User logged out: {user['email']}")
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: dict = Depends(require_auth)):
    """
    Get the current authenticated user's information.
    """
    return UserResponse(
        user_id=user["user_id"],
        email=user["email"],
        full_name=user["full_name"],
        role=user["role"],
        is_active=user["is_active"],
        created_at=user["created_at"],
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(request: UserCreate):
    """
    Register a new user.
    
    Note: In production, this should be restricted to admins or require email verification.
    """
    if not AUTH_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not available",
        )
    
    store = get_user_store()
    
    # Check if email already exists
    if store.get_user_by_email(request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create user
    user = store.create_user(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )
    
    logger.info(f"New user registered: {request.email}")
    
    return UserResponse(
        user_id=user["user_id"],
        email=user["email"],
        full_name=user["full_name"],
        role=user["role"],
        is_active=user["is_active"],
        created_at=user["created_at"],
    )


@router.get("/status")
async def auth_status():
    """
    Check authentication service status.
    """
    return {
        "available": AUTH_AVAILABLE,
        "demo_credentials": {
            "email": "demo@example.com",
            "password": "demo123",
        } if AUTH_AVAILABLE else None,
        "message": "Auth available" if AUTH_AVAILABLE else "Install python-jose and passlib to enable auth",
    }

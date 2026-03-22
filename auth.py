"""
auth.py
-------
Authentication router: signup, login, current-user, and admin endpoints.
"""

from datetime import datetime, timezone, timedelta
from typing import Annotated

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, field_validator

from config import get_settings
from db import users_collection

settings = get_settings()

# ---------------------------------------------------------------------------
# Security primitives
# ---------------------------------------------------------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

ADMIN_EMAIL = "jayshreethakre19@gmail.com"  # change this to your admin email


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, role: str = "user") -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": subject, "exp": expire, "role": role}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        email: str | None = payload.get("sub")
        if not email:
            raise credentials_exc
        return {"email": email, "role": payload.get("role", "user")}
    except JWTError:
        raise credentials_exc


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class SignupRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str = "user"


class MessageResponse(BaseModel):
    msg: str


class UserResponse(BaseModel):
    email: str
    role: str


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> str:
    data = decode_access_token(token)
    return data["email"]


def get_current_user_with_role(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    return decode_access_token(token)


def require_admin(user: Annotated[dict, Depends(get_current_user_with_role)]) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(tags=["Authentication"])


@router.post("/signup", response_model=MessageResponse, status_code=201)
def signup(payload: SignupRequest) -> MessageResponse:
    if users_collection.find_one({"email": payload.email}):
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    role = "admin" if payload.email == ADMIN_EMAIL else "user"

    users_collection.insert_one({
        "email": payload.email,
        "hashed_password": hash_password(payload.password),
        "role": role,
        "created_at": datetime.now(timezone.utc),
    })
    return MessageResponse(msg="Account created successfully")


@router.post("/login", response_model=TokenResponse)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> TokenResponse:
    user = users_collection.find_one({"email": form_data.username})

    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role = user.get("role", "user")
    token = create_access_token(subject=user["email"], role=role)
    return TokenResponse(access_token=token, role=role)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: Annotated[dict, Depends(get_current_user_with_role)]) -> UserResponse:
    return UserResponse(email=current_user["email"], role=current_user["role"])

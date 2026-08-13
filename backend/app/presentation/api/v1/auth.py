from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.login_user import InvalidCredentialsError, login_user
from app.application.use_cases.register_user import (
    EmailAlreadyRegisteredError,
    register_user,
)
from app.infrastructure.db.models.user import User
from app.infrastructure.db.repositories.user_repository import UserRepository
from app.infrastructure.db.session import get_db
from app.presentation.api.v1.deps import get_current_user
from app.presentation.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    try:
        result = await register_user(repo, payload.email, payload.password)
    except EmailAlreadyRegisteredError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered") from e
    return TokenResponse(access_token=result.access_token)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    try:
        result = await login_user(repo, payload.email, payload.password)
    except InvalidCredentialsError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password") from e
    return TokenResponse(access_token=result.access_token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return UserResponse(id=current_user.id, email=current_user.email, role=current_user.role)
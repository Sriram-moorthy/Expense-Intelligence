from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201, response_model=UserResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
    return AuthService(db).register(
        username=payload.username,
        email=payload.email,
        password=payload.password,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    description=(
        "Authenticate with email and password and return a JWT access token. "
        "Logout is client-side token removal; V1 JWTs are stateless and are "
        "not revoked on the server."
    ),
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    access_token = AuthService(db).login(
        email=payload.email,
        password=payload.password,
    )
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserResponse,
    description=(
        "Return the authenticated user identified by the Bearer access token. "
        "Logout is client-side token removal; V1 JWTs are stateless and are "
        "not revoked on the server."
    ),
)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user

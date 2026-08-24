from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.exceptions import UNAUTHENTICATED, AppError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
        or not credentials.credentials
    ):
        raise AppError(401, UNAUTHENTICATED, "Authentication required")

    try:
        payload = decode_access_token(credentials.credentials)
        subject = payload.get("sub")
        user_id = int(subject)
    except (InvalidTokenError, TypeError, ValueError, AttributeError):
        raise AppError(401, UNAUTHENTICATED, "Authentication required")

    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise AppError(401, UNAUTHENTICATED, "Authentication required")
    return user

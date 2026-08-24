from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    AUTHENTICATION_FAILED,
    EMAIL_ALREADY_EXISTS,
    USERNAME_ALREADY_EXISTS,
    AppError,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user import UserRepository


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def register(self, username: str, email: str, password: str) -> User:
        if self.users.get_by_username(username) is not None:
            raise AppError(
                409,
                USERNAME_ALREADY_EXISTS,
                "Username already exists",
            )
        if self.users.get_by_email(email) is not None:
            raise AppError(
                409,
                EMAIL_ALREADY_EXISTS,
                "Email already exists",
            )

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
        )
        self.users.add(user)
        try:
            self.db.commit()
            self.db.refresh(user)
        except IntegrityError:
            self.db.rollback()
            raise self._conflict_from_integrity_error(username, email) from None
        return user

    def login(self, email: str, password: str) -> str:
        user = self.users.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise AppError(
                401,
                AUTHENTICATION_FAILED,
                "Invalid email or password",
            )
        return create_access_token(str(user.id))

    def _conflict_from_integrity_error(self, username: str, email: str) -> AppError:
        if self.users.get_by_username(username) is not None:
            return AppError(409, USERNAME_ALREADY_EXISTS, "Username already exists")
        if self.users.get_by_email(email) is not None:
            return AppError(409, EMAIL_ALREADY_EXISTS, "Email already exists")
        return AppError(409, EMAIL_ALREADY_EXISTS, "Email already exists")

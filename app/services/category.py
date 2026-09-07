from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    CATEGORY_ALREADY_EXISTS,
    CATEGORY_IN_USE,
    CATEGORY_NOT_FOUND,
    AppError,
)
from app.models.category import Category
from app.repositories.category import CategoryRepository


class CategoryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.categories = CategoryRepository(db)

    def create(self, user_id: int, name: str, category_type: str) -> Category:
        if self.categories.get_by_user_and_name(user_id, name) is not None:
            raise AppError(
                409,
                CATEGORY_ALREADY_EXISTS,
                "Category name already exists",
            )

        category = Category(user_id=user_id, name=name, type=category_type)
        self.categories.add(category)
        try:
            self.db.commit()
            self.db.refresh(category)
        except IntegrityError:
            self.db.rollback()
            raise self._conflict_from_integrity_error(user_id, name) from None
        return category

    def list_for_user(self, user_id: int) -> list[Category]:
        return self.categories.get_all_for_user(user_id)

    def get_for_user(self, user_id: int, category_id: int) -> Category:
        return self._owned_category(user_id, category_id)

    def update(
        self, user_id: int, category_id: int, name: str, category_type: str
    ) -> Category:
        category = self._owned_category(user_id, category_id)
        existing = self.categories.get_by_user_and_name(user_id, name)
        if existing is not None and existing.id != category.id:
            raise AppError(
                409,
                CATEGORY_ALREADY_EXISTS,
                "Category name already exists",
            )

        category.name = name
        category.type = category_type
        category.updated_at = datetime.now(timezone.utc)
        try:
            self.db.commit()
            self.db.refresh(category)
        except IntegrityError:
            self.db.rollback()
            raise self._conflict_from_integrity_error(user_id, name) from None
        return category

    def delete(self, user_id: int, category_id: int) -> None:
        category = self._owned_category(user_id, category_id)
        self.categories.delete(category)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise AppError(
                409,
                CATEGORY_IN_USE,
                "Category cannot be deleted while in use",
            ) from None

    def _owned_category(self, user_id: int, category_id: int) -> Category:
        category = self.categories.get_by_id_for_user(category_id, user_id)
        if category is None:
            raise AppError(404, CATEGORY_NOT_FOUND, "Category not found")
        return category

    def _conflict_from_integrity_error(self, user_id: int, name: str) -> AppError:
        if self.categories.get_by_user_and_name(user_id, name) is not None:
            return AppError(
                409,
                CATEGORY_ALREADY_EXISTS,
                "Category name already exists",
            )
        return AppError(
            409,
            CATEGORY_ALREADY_EXISTS,
            "Category name already exists",
        )

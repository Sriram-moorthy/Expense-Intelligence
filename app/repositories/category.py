from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category


class CategoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, category_id: int) -> Category | None:
        return self.db.get(Category, category_id)

    def get_by_id_for_user(self, category_id: int, user_id: int) -> Category | None:
        return self.db.scalar(
            select(Category).where(
                Category.id == category_id,
                Category.user_id == user_id,
            )
        )

    def get_all_for_user(self, user_id: int) -> list[Category]:
        return list(
            self.db.scalars(
                select(Category)
                .where(Category.user_id == user_id)
                .order_by(Category.id)
            ).all()
        )

    def get_by_user_and_name(self, user_id: int, name: str) -> Category | None:
        return self.db.scalar(
            select(Category).where(
                Category.user_id == user_id,
                Category.name == name,
            )
        )

    def add(self, category: Category) -> Category:
        self.db.add(category)
        return category

    def delete(self, category: Category) -> None:
        self.db.delete(category)

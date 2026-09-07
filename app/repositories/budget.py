from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.budget import Budget


class BudgetRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, budget_id: int) -> Budget | None:
        return self.db.get(Budget, budget_id)

    def get_by_id_for_user(self, budget_id: int, user_id: int) -> Budget | None:
        return self.db.scalar(
            select(Budget).where(
                Budget.id == budget_id,
                Budget.user_id == user_id,
            )
        )

    def get_all_for_user(self, user_id: int) -> list[Budget]:
        return list(
            self.db.scalars(
                select(Budget).where(Budget.user_id == user_id).order_by(Budget.id)
            ).all()
        )

    def get_by_user_category_month(
        self, user_id: int, category_id: int, month: date
    ) -> Budget | None:
        return self.db.scalar(
            select(Budget).where(
                Budget.user_id == user_id,
                Budget.category_id == category_id,
                Budget.month == month,
            )
        )

    def add(self, budget: Budget) -> Budget:
        self.db.add(budget)
        return budget

    def delete(self, budget: Budget) -> None:
        self.db.delete(budget)

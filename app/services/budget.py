from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BUDGET_ALREADY_EXISTS,
    BUDGET_NOT_FOUND,
    BUDGET_REQUIRES_EXPENSE_CATEGORY,
    CATEGORY_NOT_FOUND,
    AppError,
)
from app.models.budget import Budget
from app.repositories.budget import BudgetRepository
from app.repositories.category import CategoryRepository


class BudgetService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.budgets = BudgetRepository(db)
        self.categories = CategoryRepository(db)

    def create(
        self, user_id: int, category_id: int, amount: Decimal, month: date
    ) -> Budget:
        self._owned_expense_category(user_id, category_id)
        if (
            self.budgets.get_by_user_category_month(user_id, category_id, month)
            is not None
        ):
            raise AppError(
                409,
                BUDGET_ALREADY_EXISTS,
                "Budget already exists for this category and month",
            )

        budget = Budget(
            user_id=user_id,
            category_id=category_id,
            amount=amount,
            month=month,
        )
        self.budgets.add(budget)
        try:
            self.db.commit()
            self.db.refresh(budget)
        except IntegrityError:
            self.db.rollback()
            raise self._conflict_from_integrity_error(
                user_id, category_id, month
            ) from None
        return budget

    def list_for_user(self, user_id: int) -> list[Budget]:
        return self.budgets.get_all_for_user(user_id)

    def get_for_user(self, user_id: int, budget_id: int) -> Budget:
        return self._owned_budget(user_id, budget_id)

    def update(
        self,
        user_id: int,
        budget_id: int,
        category_id: int,
        amount: Decimal,
        month: date,
    ) -> Budget:
        budget = self._owned_budget(user_id, budget_id)
        self._owned_expense_category(user_id, category_id)
        existing = self.budgets.get_by_user_category_month(user_id, category_id, month)
        if existing is not None and existing.id != budget.id:
            raise AppError(
                409,
                BUDGET_ALREADY_EXISTS,
                "Budget already exists for this category and month",
            )

        budget.category_id = category_id
        budget.amount = amount
        budget.month = month
        budget.updated_at = datetime.now(timezone.utc)
        try:
            self.db.commit()
            self.db.refresh(budget)
        except IntegrityError:
            self.db.rollback()
            raise self._conflict_from_integrity_error(
                user_id, category_id, month
            ) from None
        return budget

    def delete(self, user_id: int, budget_id: int) -> None:
        budget = self._owned_budget(user_id, budget_id)
        self.budgets.delete(budget)
        self.db.commit()

    def _owned_budget(self, user_id: int, budget_id: int) -> Budget:
        budget = self.budgets.get_by_id_for_user(budget_id, user_id)
        if budget is None:
            raise AppError(404, BUDGET_NOT_FOUND, "Budget not found")
        return budget

    def _owned_expense_category(self, user_id: int, category_id: int) -> None:
        category = self.categories.get_by_id_for_user(category_id, user_id)
        if category is None:
            raise AppError(404, CATEGORY_NOT_FOUND, "Category not found")
        if category.type != "EXPENSE":
            raise AppError(
                400,
                BUDGET_REQUIRES_EXPENSE_CATEGORY,
                "Budget can only be created for an expense category",
            )

    def _conflict_from_integrity_error(
        self, user_id: int, category_id: int, month: date
    ) -> AppError:
        if (
            self.budgets.get_by_user_category_month(user_id, category_id, month)
            is not None
        ):
            return AppError(
                409,
                BUDGET_ALREADY_EXISTS,
                "Budget already exists for this category and month",
            )
        return AppError(404, CATEGORY_NOT_FOUND, "Category not found")

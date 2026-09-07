from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    CATEGORY_NOT_FOUND,
    TRANSACTION_NOT_FOUND,
    TRANSACTION_TYPE_MISMATCH,
    AppError,
)
from app.models.transaction import Transaction
from app.repositories.category import CategoryRepository
from app.repositories.transaction import TransactionRepository


class TransactionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.transactions = TransactionRepository(db)
        self.categories = CategoryRepository(db)

    def create(
        self,
        user_id: int,
        amount: Decimal,
        transaction_type: str,
        category_id: int,
        description: str | None,
        transaction_date: date,
    ) -> Transaction:
        self._owned_matching_category(user_id, category_id, transaction_type)
        transaction = Transaction(
            user_id=user_id,
            category_id=category_id,
            amount=amount,
            type=transaction_type,
            description=description,
            transaction_date=transaction_date,
        )
        self.transactions.add(transaction)
        try:
            self.db.commit()
            self.db.refresh(transaction)
        except IntegrityError:
            self.db.rollback()
            raise AppError(404, CATEGORY_NOT_FOUND, "Category not found") from None
        return transaction

    def list_for_user(self, user_id: int) -> list[Transaction]:
        return self.transactions.get_all_for_user(user_id)

    def get_for_user(self, user_id: int, transaction_id: int) -> Transaction:
        return self._owned_transaction(user_id, transaction_id)

    def update(
        self,
        user_id: int,
        transaction_id: int,
        amount: Decimal,
        transaction_type: str,
        category_id: int,
        description: str | None,
        transaction_date: date,
    ) -> Transaction:
        transaction = self._owned_transaction(user_id, transaction_id)
        self._owned_matching_category(user_id, category_id, transaction_type)
        transaction.amount = amount
        transaction.type = transaction_type
        transaction.category_id = category_id
        transaction.description = description
        transaction.transaction_date = transaction_date
        transaction.updated_at = datetime.now(timezone.utc)
        try:
            self.db.commit()
            self.db.refresh(transaction)
        except IntegrityError:
            self.db.rollback()
            raise AppError(404, CATEGORY_NOT_FOUND, "Category not found") from None
        return transaction

    def delete(self, user_id: int, transaction_id: int) -> None:
        transaction = self._owned_transaction(user_id, transaction_id)
        self.transactions.delete(transaction)
        self.db.commit()

    def _owned_transaction(self, user_id: int, transaction_id: int) -> Transaction:
        transaction = self.transactions.get_by_id_for_user(transaction_id, user_id)
        if transaction is None:
            raise AppError(404, TRANSACTION_NOT_FOUND, "Transaction not found")
        return transaction

    def _owned_matching_category(
        self, user_id: int, category_id: int, transaction_type: str
    ) -> None:
        category = self.categories.get_by_id_for_user(category_id, user_id)
        if category is None:
            raise AppError(404, CATEGORY_NOT_FOUND, "Category not found")
        if category.type != transaction_type:
            raise AppError(
                400,
                TRANSACTION_TYPE_MISMATCH,
                "Transaction type must match category type",
            )

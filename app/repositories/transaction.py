from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction


class TransactionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, transaction_id: int) -> Transaction | None:
        return self.db.get(Transaction, transaction_id)

    def get_by_id_for_user(
        self, transaction_id: int, user_id: int
    ) -> Transaction | None:
        return self.db.scalar(
            select(Transaction).where(
                Transaction.id == transaction_id,
                Transaction.user_id == user_id,
            )
        )

    def get_all_for_user(self, user_id: int) -> list[Transaction]:
        return list(
            self.db.scalars(
                select(Transaction)
                .where(Transaction.user_id == user_id)
                .order_by(Transaction.id)
            ).all()
        )

    def add(self, transaction: Transaction) -> Transaction:
        self.db.add(transaction)
        return transaction

    def delete(self, transaction: Transaction) -> None:
        self.db.delete(transaction)

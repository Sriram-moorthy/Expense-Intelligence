from datetime import date

from sqlalchemy import func, select
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

    def list_for_user(
        self,
        user_id: int,
        *,
        transaction_type: str | None,
        category_id: int | None,
        start_date: date | None,
        end_date: date | None,
        sort_by: str,
        sort_order: str,
        page: int,
        page_size: int,
    ) -> tuple[list[Transaction], int]:
        filters = self._filters(
            user_id,
            transaction_type=transaction_type,
            category_id=category_id,
            start_date=start_date,
            end_date=end_date,
        )
        total = int(
            self.db.scalar(select(func.count()).select_from(Transaction).where(*filters))
            or 0
        )
        stmt = (
            select(Transaction)
            .where(*filters)
            .order_by(*self._order_by(sort_by, sort_order))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(stmt).all()), total

    def add(self, transaction: Transaction) -> Transaction:
        self.db.add(transaction)
        return transaction

    def delete(self, transaction: Transaction) -> None:
        self.db.delete(transaction)

    def _filters(
        self,
        user_id: int,
        *,
        transaction_type: str | None,
        category_id: int | None,
        start_date: date | None,
        end_date: date | None,
    ) -> list:
        filters = [Transaction.user_id == user_id]
        if transaction_type is not None:
            filters.append(Transaction.type == transaction_type)
        if category_id is not None:
            filters.append(Transaction.category_id == category_id)
        if start_date is not None:
            filters.append(Transaction.transaction_date >= start_date)
        if end_date is not None:
            filters.append(Transaction.transaction_date <= end_date)
        return filters

    def _order_by(self, sort_by: str, sort_order: str):
        column = (
            Transaction.transaction_date
            if sort_by == "transaction_date"
            else Transaction.amount
        )
        if sort_order == "desc":
            return (column.desc(), Transaction.id.desc())
        return (column.asc(), Transaction.id.asc())

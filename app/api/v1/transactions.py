from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.category import CategoryType
from app.schemas.transaction import (
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
    TransactionUpdate,
)
from app.services.transaction import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])

SortBy = Literal["transaction_date", "amount"]
SortOrder = Literal["asc", "desc"]


@router.post("", status_code=201, response_model=TransactionResponse)
def create_transaction(
    payload: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Transaction:
    return TransactionService(db).create(
        user_id=current_user.id,
        amount=payload.amount,
        transaction_type=payload.type,
        category_id=payload.category_id,
        description=payload.description,
        transaction_date=payload.transaction_date,
    )


@router.get("", response_model=TransactionListResponse)
def list_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    type: CategoryType | None = None,
    category_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    sort_by: SortBy = "transaction_date",
    sort_order: SortOrder = "desc",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> TransactionListResponse:
    items, total, pages = TransactionService(db).list_for_user(
        current_user.id,
        transaction_type=type,
        category_id=category_id,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    return TransactionListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Transaction:
    return TransactionService(db).get_for_user(current_user.id, transaction_id)


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    payload: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Transaction:
    return TransactionService(db).update(
        user_id=current_user.id,
        transaction_id=transaction_id,
        amount=payload.amount,
        transaction_type=payload.type,
        category_id=payload.category_id,
        description=payload.description,
        transaction_date=payload.transaction_date,
    )


@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    TransactionService(db).delete(current_user.id, transaction_id)
    return Response(status_code=204)

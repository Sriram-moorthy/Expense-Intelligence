from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)
from app.services.transaction import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


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


@router.get("", response_model=list[TransactionResponse])
def list_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Transaction]:
    return TransactionService(db).list_for_user(current_user.id)


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

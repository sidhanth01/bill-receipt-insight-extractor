# backend/database/crud.py

from sqlmodel import Session, select
from backend.database.models import Receipt, engine
from typing import List, Optional
from datetime import date

def create_receipt(receipt: Receipt) -> Receipt:
    """
    Adds a new receipt entry to the database.
    """
    with Session(engine) as session:
        session.add(receipt)
        session.commit()
        session.refresh(receipt) # Refresh to get the generated ID
        return receipt

def get_receipts(
    skip: int = 0,
    limit: int = 100,
    vendor: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    category: Optional[str] = None
) -> List[Receipt]:
    """
    Retrieves a list of receipts from the database, with optional filtering.
    """
    with Session(engine) as session:
        query = select(Receipt)
        if vendor:
            query = query.where(Receipt.vendor.ilike(f"%{vendor}%")) # Case-insensitive partial match
        if start_date:
            query = query.where(Receipt.transaction_date >= start_date)
        if end_date:
            query = query.where(Receipt.transaction_date <= end_date)
        if min_amount is not None:
            query = query.where(Receipt.amount >= min_amount)
        if max_amount is not None:
            query = query.where(Receipt.amount <= max_amount)
        if category:
            query = query.where(Receipt.category.ilike(f"%{category}%"))

        # Apply pagination
        query = query.offset(skip).limit(limit)

        receipts = session.exec(query).all()
        return receipts

def get_receipt_by_id(receipt_id: int) -> Optional[Receipt]:
    """
    Retrieves a single receipt by its ID.
    """
    with Session(engine) as session:
        receipt = session.get(Receipt, receipt_id)
        return receipt

def update_receipt(receipt_id: int, receipt_data: dict) -> Optional[Receipt]:
    """
    Updates an existing receipt entry in the database.
    `receipt_data` should be a dictionary of fields to update.
    """
    with Session(engine) as session:
        receipt = session.get(Receipt, receipt_id)
        if not receipt:
            return None
        
        # Update attributes from the provided dictionary
        for key, value in receipt_data.items():
            setattr(receipt, key, value)
        
        session.add(receipt) # Add back to session to mark as dirty
        session.commit()
        session.refresh(receipt)
        return receipt

def delete_receipt(receipt_id: int) -> bool:
    """
    Deletes a receipt entry from the database by its ID.
    Returns True if deleted, False if not found.
    """
    with Session(engine) as session:
        receipt = session.get(Receipt, receipt_id)
        if not receipt:
            return False
        session.delete(receipt)
        session.commit()
        return True
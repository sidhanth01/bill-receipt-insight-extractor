# backend/core/validation.py

from pydantic import BaseModel, Field, ValidationError
from datetime import date
from typing import Optional, Literal

class ReceiptBase(BaseModel):
    """Base model for receipt data, defining common fields."""
    vendor: str = Field(..., min_length=1, description="Name of the vendor or biller.")
    transaction_date: date = Field(..., description="Date of the transaction or billing period.")
    amount: float = Field(..., gt=0, description="Amount of the transaction, must be greater than 0.")
    category: Optional[str] = Field(None, description="Optional category for the transaction (e.g., Groceries, Utilities).")

class ReceiptCreate(ReceiptBase):
    """Model for creating a new receipt, extending ReceiptBase."""
    original_filename: str = Field(..., description="Original filename of the uploaded receipt.")

class ReceiptRead(ReceiptBase):
    """Model for reading receipt data, includes ID and filename."""
    id: int
    original_filename: str

class ReceiptUpdate(BaseModel):
    """Model for updating an existing receipt, all fields are optional."""
    vendor: Optional[str] = Field(None, min_length=1, description="Updated vendor name.")
    transaction_date: Optional[date] = Field(None, description="Updated transaction date.")
    amount: Optional[float] = Field(None, gt=0, description="Updated amount.")
    category: Optional[str] = Field(None, description="Updated category.")

class FileUploadResponse(BaseModel):
    """Model for the response after a file upload."""
    filename: str
    message: str
    detail: Optional[str] = None
    parsed_data: Optional[ReceiptRead] = None # Include parsed data if successful

class ErrorResponse(BaseModel):
    """Model for a generic error response."""
    message: str
    detail: Optional[str] = None

class SearchQuery(BaseModel):
    """Model for search parameters."""
    vendor: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    category: Optional[str] = None
    skip: int = 0
    limit: int = 100

class SortOrder(BaseModel):
    """Model for sorting parameters."""
    field: Literal["vendor", "transaction_date", "amount", "category"]
    direction: Literal["asc", "desc"] = "asc"

# Example usage (for testing validation)
if __name__ == "__main__":
    try:
        # Valid data
        receipt_data_valid = {
            "vendor": "SuperMart",
            "transaction_date": "2025-07-19",
            "amount": 123.45,
            "category": "Groceries",
            "original_filename": "receipt_1.jpg"
        }
        receipt = ReceiptCreate(**receipt_data_valid)
        print(f"Valid Receipt: {receipt}")

        # Invalid data (amount <= 0)
        receipt_data_invalid_amount = {
            "vendor": "Cafe XYZ",
            "transaction_date": "2025-07-20",
            "amount": -10.0,
            "original_filename": "cafe_bill.png"
        }
        try:
            ReceiptCreate(**receipt_data_invalid_amount)
        except ValidationError as e:
            print(f"\nValidation Error (Amount): {e.errors()}")

        # Invalid data (missing vendor)
        receipt_data_invalid_vendor = {
            "transaction_date": "2025-07-21",
            "amount": 50.0,
            "original_filename": "missing_vendor.txt"
        }
        try:
            ReceiptCreate(**receipt_data_invalid_vendor)
        except ValidationError as e:
            print(f"\nValidation Error (Vendor): {e.errors()}")

    except ValidationError as e:
        print(f"Unexpected Validation Error: {e}")
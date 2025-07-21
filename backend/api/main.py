# backend/api/main.py

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import JSONResponse, StreamingResponse # Added StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import date, datetime # Import datetime for type checking
import os
import shutil
import io # Added io
import pandas as pd # Added pandas

# Import database models and CRUD operations
from backend.database.models import create_db_and_tables, Receipt
from backend.database import crud

# Import core logic (validation, parser, algorithms)
from backend.core.validation import (
    ReceiptCreate, ReceiptRead, ReceiptUpdate,
    FileUploadResponse, ErrorResponse, SearchQuery, SortOrder
)
from backend.core.parser import ReceiptParser
from backend.core.algorithms import (
    perform_search, perform_sort, # In-memory algorithms
    calculate_aggregates, get_vendor_frequency, get_monthly_spend
)

# Initialize FastAPI app
app = FastAPI(
    title="Bill & Receipt Insight Extractor API",
    description="API for uploading receipts, extracting data, and getting financial insights.",
    version="1.0.0",
)

# Configure CORS (Cross-Origin Resource Sharing)
# This is crucial for allowing your Streamlit frontend (running on a different port)
# to make requests to your FastAPI backend.
origins = [
    "http://localhost",
    "http://localhost:8501", # Default Streamlit port
    "http://127.0.0.1:8501", # Also common for localhost
    # Add other origins here if deploying to a specific domain later
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"], # Allows all headers
)

# Initialize ReceiptParser
receipt_parser = ReceiptParser()

# Directory to temporarily store uploaded files (optional, not strictly used for storage in this version)
# UPLOAD_DIR = "data"
# os.makedirs(UPLOAD_DIR, exist_ok=True) # Ensure the directory exists

@app.on_event("startup")
def on_startup():
    """
    Event handler that runs when the FastAPI application starts up.
    Used to create database tables if they don't exist.
    """
    create_db_and_tables()
    print("Database tables checked/created on startup.")

@app.post(
    "/upload-receipt/",
    response_model=FileUploadResponse,
    status_code=201, # 201 Created
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def upload_receipt(file: UploadFile = File(...)):
    """
    Uploads a receipt/bill file, parses it, validates data, and stores it in the database.
    Supports JPG, PNG, PDF, TXT.
    """
    file_extension = os.path.splitext(file.filename)[1].lower()
    allowed_extensions = [".jpg", ".jpeg", ".png", ".pdf", ".txt"]

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_extension}. Allowed: {', '.join(allowed_extensions)}"
        )

    # Read file content
    file_bytes = await file.read()

    try:
        # Parse the file content using the ReceiptParser
        parsed_data = receipt_parser.parse_file(file_bytes, file_extension)

        # Ensure transaction_date is a date object for Pydantic/SQLModel
        if 'transaction_date' in parsed_data and isinstance(parsed_data['transaction_date'], datetime):
            parsed_data['transaction_date'] = parsed_data['transaction_date'].date()
        elif 'transaction_date' in parsed_data and isinstance(parsed_data['transaction_date'], str):
            try:
                parsed_data['transaction_date'] = datetime.strptime(parsed_data['transaction_date'], "%Y-%m-%d").date()
            except ValueError:
                # If date string can't be parsed, set to today's date or handle as error
                parsed_data['transaction_date'] = date.today() # Fallback
        elif 'transaction_date' not in parsed_data or parsed_data['transaction_date'] is None:
            parsed_data['transaction_date'] = date.today() # Default to today if not found

        # Ensure amount is a float, default to 0.0 if not found or invalid
        if 'amount' not in parsed_data or not isinstance(parsed_data['amount'], (int, float)):
            parsed_data['amount'] = 0.0 # Default to 0.0 if not found or invalid type

        # Create a ReceiptCreate instance for Pydantic validation
        receipt_create_data = ReceiptCreate(
            vendor=parsed_data.get("vendor", "Unknown"),
            transaction_date=parsed_data.get("transaction_date"),
            amount=parsed_data.get("amount"),
            category=parsed_data.get("category", "Uncategorized"),
            original_filename=file.filename
        )

        # Create Receipt ORM object and save to DB using CRUD function
        db_receipt = Receipt(**receipt_create_data.model_dump()) # model_dump() converts Pydantic model to dict
        new_receipt = crud.create_receipt(db_receipt)

        return FileUploadResponse(
            filename=file.filename,
            message="File uploaded and parsed successfully!",
            parsed_data=ReceiptRead.model_validate(new_receipt.model_dump()) # Changed here!
        )

    except ValueError as e:
        # Catch errors from parser or Pydantic validation
        raise HTTPException(status_code=400, detail=f"Parsing or validation error: {e}")
    except Exception as e:
        # Catch any other unexpected errors during processing
        print(f"Unhandled error during upload: {e}") # Log the error for debugging
        raise HTTPException(status_code=500, detail=f"Internal server error during processing: {e}")

@app.get(
    "/receipts/",
    response_model=List[ReceiptRead],
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
def read_receipts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
    vendor: Optional[str] = Query(None, description="Filter by vendor name (partial match)"),
    start_date: Optional[date] = Query(None, description="Filter by transaction date (start)"),
    end_date: Optional[date] = Query(None, description="Filter by transaction date (end)"),
    min_amount: Optional[float] = Query(None, ge=0, description="Filter by minimum amount"),
    max_amount: Optional[float] = Query(None, ge=0, description="Filter by maximum amount"),
    category: Optional[str] = Query(None, description="Filter by category (partial match)")
):
    """
    Retrieve a list of receipts with optional filtering and pagination.
    This endpoint leverages database-level search via crud.get_receipts.
    """
    try:
        receipts = crud.get_receipts(
            skip=skip, limit=limit,
            vendor=vendor, start_date=start_date, end_date=end_date,
            min_amount=min_amount, max_amount=max_amount, category=category
        )
        # FIX: Convert each ORM object to a dictionary before Pydantic validation
        return [ReceiptRead.model_validate(r.model_dump()) for r in receipts]
    except Exception as e:
        print(f"Error retrieving receipts: {e}") # Log the error
        raise HTTPException(status_code=500, detail=f"Error retrieving receipts: {e}")

@app.get(
    "/receipts/{receipt_id}",
    response_model=ReceiptRead,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
def read_receipt_by_id(receipt_id: int):
    """
    Retrieve a single receipt by its ID.
    """
    receipt = crud.get_receipt_by_id(receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return ReceiptRead.model_validate(receipt.model_dump()) # Also convert here

@app.put(
    "/receipts/{receipt_id}",
    response_model=ReceiptRead,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
def update_existing_receipt(receipt_id: int, receipt: ReceiptUpdate):
    """
    Update an existing receipt entry.
    """
    try:
        # Convert date to date object if provided as string in update
        update_data = receipt.model_dump(exclude_unset=True)
        if 'transaction_date' in update_data and isinstance(update_data['transaction_date'], str):
            try:
                update_data['transaction_date'] = datetime.strptime(update_data['transaction_date'], "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

        updated_receipt = crud.update_receipt(receipt_id, update_data)
        if not updated_receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        # FIX: Convert the updated_receipt ORM object to a dictionary before Pydantic validation
        return ReceiptRead.model_validate(updated_receipt.model_dump()) # Changed here!
    except HTTPException: # Re-raise HTTPExceptions directly
        raise
    except Exception as e:
        print(f"Error updating receipt: {e}") # Log the error
        raise HTTPException(status_code=500, detail=f"Error updating receipt: {e}")

@app.delete(
    "/receipts/{receipt_id}",
    status_code=204, # 204 No Content for successful deletion
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
def delete_existing_receipt(receipt_id: int):
    """
    Delete a receipt entry.
    """
    try:
        deleted = crud.delete_receipt(receipt_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Receipt not found")
        return JSONResponse(status_code=204, content={"message": "Receipt deleted successfully"})
    except Exception as e:
        print(f"Error deleting receipt: {e}") # Log the error
        raise HTTPException(status_code=500, detail=f"Error deleting receipt: {e}")

# --- NEW EXPORT ENDPOINTS ---
@app.get("/export/csv/", responses={200: {"content": {"text/csv": {}}}, 500: {"model": ErrorResponse}})
async def export_receipts_csv(
    vendor: Optional[str] = Query(None, description="Filter by vendor name (partial match)"),
    start_date: Optional[date] = Query(None, description="Filter by transaction date (start)"),
    end_date: Optional[date] = Query(None, description="Filter by transaction date (end)"),
    min_amount: Optional[float] = Query(None, ge=0, description="Filter by minimum amount"),
    max_amount: Optional[float] = Query(None, ge=0, description="Filter by maximum amount"),
    category: Optional[str] = Query(None, description="Filter by category (partial match)")
):
    """
    Exports filtered receipts data as a CSV file.
    """
    try:
        # Fetch all receipts (or a large limit) based on current filters
        receipts = crud.get_receipts(
            skip=0, limit=10000, # Fetch a large enough set for export
            vendor=vendor, start_date=start_date, end_date=end_date,
            min_amount=min_amount, max_amount=max_amount, category=category
        )
        
        if not receipts:
            raise HTTPException(status_code=404, detail="No receipts found to export.")

        # Convert ORM objects to dictionaries for DataFrame creation
        receipts_data = [r.model_dump() for r in receipts]
        df = pd.DataFrame(receipts_data)

        # Drop the 'id' column as it's typically not needed in exports
        if 'id' in df.columns:
            df = df.drop(columns=['id'])
        
        # Convert transaction_date to string format for CSV
        if 'transaction_date' in df.columns:
            # Ensure it's datetime first, then format
            df['transaction_date'] = pd.to_datetime(df['transaction_date']).dt.strftime('%Y-%m-%d')

        # Create a StringIO buffer to hold the CSV data
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0) # Rewind the buffer to the beginning

        # Return as StreamingResponse with CSV content type and download header
        headers = {
            "Content-Disposition": "attachment; filename=receipts_export.csv",
            "Content-Type": "text/csv"
        }
        return StreamingResponse(iter([buffer.getvalue()]), headers=headers, media_type="text/csv")
    except HTTPException:
        raise # Re-raise HTTPExceptions
    except Exception as e:
        print(f"Error exporting CSV: {e}")
        raise HTTPException(status_code=500, detail=f"Error exporting CSV: {e}")

@app.get("/export/json/", responses={200: {"content": {"application/json": {}}}, 500: {"model": ErrorResponse}})
async def export_receipts_json(
    vendor: Optional[str] = Query(None, description="Filter by vendor name (partial match)"),
    start_date: Optional[date] = Query(None, description="Filter by transaction date (start)"),
    end_date: Optional[date] = Query(None, description="Filter by transaction date (end)"),
    min_amount: Optional[float] = Query(None, ge=0, description="Filter by minimum amount"),
    max_amount: Optional[float] = Query(None, ge=0, description="Filter by maximum amount"),
    category: Optional[str] = Query(None, description="Filter by category (partial match)")
):
    """
    Exports filtered receipts data as a JSON file.
    """
    try:
        receipts = crud.get_receipts(
            skip=0, limit=10000, # Fetch a large enough set for export
            vendor=vendor, start_date=start_date, end_date=end_date,
            min_amount=min_amount, max_amount=max_amount, category=category
        )
        
        if not receipts:
            raise HTTPException(status_code=404, detail="No receipts found to export.")

        receipts_data = [r.model_dump() for r in receipts]
        df = pd.DataFrame(receipts_data)

        # Convert transaction_date to string format for JSON
        if 'transaction_date' in df.columns:
            # Ensure it's datetime first, then format
            df['transaction_date'] = pd.to_datetime(df['transaction_date']).dt.strftime('%Y-%m-%d')

        # Create a StringIO buffer to hold the JSON data
        buffer = io.StringIO()
        df.to_json(buffer, orient="records", indent=4) # orient="records" for list of objects
        buffer.seek(0)

        headers = {
            "Content-Disposition": "attachment; filename=receipts_export.json",
            "Content-Type": "application/json"
        }
        return StreamingResponse(iter([buffer.getvalue()]), headers=headers, media_type="application/json")
    except HTTPException:
        raise # Re-raise HTTPExceptions
    except Exception as e:
        print(f"Error exporting JSON: {e}")
        raise HTTPException(status_code=500, detail=f"Error exporting JSON: {e}")
    
# Note: The /receipts/search/ and /receipts/sort/ endpoints are commented out
# because the /receipts/ GET endpoint already handles filtering directly at the DB level,
# and sorting is handled by the frontend after fetching.
# This simplifies the API and leverages DB efficiency for filtering.
# If complex in-memory search/sort logic was required beyond DB capabilities,
# these endpoints could be re-enabled and use the algorithms.py functions.


@app.get(
    "/receipts/aggregates/",
    responses={200: {"content": {"application/json": {"example": {"total_spend": 1234.56, "average_spend": 123.45, "median_spend": 100.0, "mode_spend": [50.0]}}}}, 500: {"model": ErrorResponse}}
)
def get_aggregates():
    """
    Calculate and return statistical aggregates of expenditure.
    """
    try:
        # Fetch all receipts for aggregation. Limit is set high for a mini-app.
        # For very large datasets, consider fetching in chunks or performing aggregation at DB level.
        receipts = crud.get_receipts(skip=0, limit=10000)
        if not receipts:
            return JSONResponse(content={"total_spend": 0.0, "average_spend": 0.0, "median_spend": 0.0, "mode_spend": []})

        # Filter out non-numeric amounts before passing to aggregation function
        amounts = [r.amount for r in receipts if isinstance(r.amount, (int, float))]
        
        aggregates = calculate_aggregates(amounts)
        return aggregates
    except Exception as e:
        print(f"Error calculating aggregates: {e}") # Log the error
        raise HTTPException(status_code=500, detail=f"Error calculating aggregates: {e}")

@app.get(
    "/receipts/vendor-frequency/",
    responses={200: {"content": {"application/json": {"example": {"SuperMart": 5, "Cafe XYZ": 3}}}}, 500: {"model": ErrorResponse}}
)
def get_vendor_frequencies():
    """
    Calculate and return the frequency distribution of vendors.
    """
    try:
        receipts = crud.get_receipts(skip=0, limit=10000)
        # Convert ORM objects to dictionaries or access attributes directly
        vendors = [r.vendor for r in receipts]
        frequency = get_vendor_frequency(vendors)
        return frequency
    except Exception as e:
        print(f"Error calculating vendor frequency: {e}") # Log the error
        raise HTTPException(status_code=500, detail=f"Error calculating vendor frequency: {e}")

@app.get(
    "/receipts/monthly-spend/",
    responses={200: {"content": {"application/json": {"example": {"2025-01": 500.0, "2025-02": 750.0}}}}, 500: {"model": ErrorResponse}}
)
def get_monthly_spend_trend():
    """
    Calculate and return monthly spend trends.
    """
    try:
        receipts = crud.get_receipts(skip=0, limit=10000)
        # Convert to list of dicts for easier processing by get_monthly_spend
        # Ensure transaction_date is a date object or datetime object
        receipts_data = [
            {"transaction_date": r.transaction_date, "amount": r.amount}
            for r in receipts
        ]
        monthly_spend = get_monthly_spend(receipts_data)
        return monthly_spend
    except Exception as e:
        print(f"Error calculating monthly spend: {e}") # Log the error
        raise HTTPException(status_code=500, detail=f"Error calculating monthly spend: {e}")

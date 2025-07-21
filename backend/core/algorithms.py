# backend/core/algorithms.py

from typing import List, Dict, Any, Optional, Literal
from collections import Counter
from datetime import date, datetime # Import datetime for parsing if needed
import statistics
import pandas as pd # Using pandas for aggregations and time-series for convenience

# Assuming ReceiptRead model structure is available for type hinting conceptually.
# In a real project, you might import it directly from validation.py if needed for strict typing.
# For simplicity here, we'll use Dict[str, Any] or assume a structure
# that has the necessary attributes (e.g., 'vendor', 'transaction_date', 'amount').

# --- Search Algorithms ---
def perform_search(
    data: List[Dict[str, Any]],
    vendor: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Performs in-memory search on a list of receipt data based on various criteria.
    This is a linear search implementation. For very large datasets,
    database-level filtering (as done in crud.py) is more efficient.
    """
    results = []
    for item in data:
        match = True
        
        # Vendor search (case-insensitive partial match)
        if vendor:
            item_vendor = item.get("vendor", "")
            if not isinstance(item_vendor, str) or vendor.lower() not in item_vendor.lower():
                match = False
        
        # Date range search
        item_date = item.get("transaction_date")
        if item_date: # Ensure date exists
            # Convert item_date to date object if it's a datetime or string
            if isinstance(item_date, datetime):
                item_date = item_date.date()
            elif isinstance(item_date, str):
                try:
                    item_date = datetime.strptime(item_date, "%Y-%m-%d").date()
                except ValueError:
                    item_date = None # Invalid date string, treat as no date
            
            if item_date: # Check again after potential conversion
                if start_date and item_date < start_date:
                    match = False
                if end_date and item_date > end_date:
                    match = False
            else: # If item_date couldn't be parsed or was None initially, it can't match date filters
                if start_date or end_date: # If any date filter is present, and item_date is invalid/missing
                    match = False
        else: # If item_date is None, it can't match date filters
            if start_date or end_date:
                match = False

        # Amount range search
        item_amount = item.get("amount")
        if item_amount is not None:
            if not isinstance(item_amount, (int, float)): # Ensure it's a number
                match = False # Treat non-numeric amounts as no match for amount filters
            else:
                if min_amount is not None and item_amount < min_amount:
                    match = False
                if max_amount is not None and item_amount > max_amount:
                    match = False
        else: # If item_amount is None, it can't match amount filters
            if min_amount is not None or max_amount is not None:
                match = False

        # Category search (case-insensitive partial match)
        if category:
            item_category = item.get("category", "")
            if not isinstance(item_category, str) or category.lower() not in item_category.lower():
                match = False

        if match:
            results.append(item)
    return results

# --- Sorting Algorithms ---
def perform_sort(
    data: List[Dict[str, Any]],
    field: Literal["vendor", "transaction_date", "amount", "category"],
    direction: Literal["asc", "desc"] = "asc"
) -> List[Dict[str, Any]]:
    """
    Sorts a list of receipt data in-memory based on a specified field and direction.
    Uses Python's built-in Timsort (optimized hybrid sorting algorithm).
    Time Complexity: O(n log n)
    """
    reverse = (direction == "desc")

    # Define a custom key function for sorting
    def sort_key(item):
        value = item.get(field)
        if value is None:
            # Place None values at the end regardless of sort direction
            return (True, None) if reverse else (False, None)
        
        if field in ["vendor", "category"] and isinstance(value, str):
            return (False, value.lower()) # Case-insensitive string sort
        elif field == "transaction_date":
            # Ensure date is a date object for proper comparison
            if isinstance(value, datetime):
                return (False, value.date())
            elif isinstance(value, str):
                try:
                    return (False, datetime.strptime(value, "%Y-%m-%d").date())
                except ValueError:
                    return (True, None) # Treat unparseable date strings as None for sorting
            return (False, value) # Assume it's already a date object
        else: # For amount (float/int)
            return (False, value)

    return sorted(data, key=sort_key, reverse=reverse)

# --- Aggregation Functions ---
def calculate_aggregates(amounts: List[float]) -> Dict[str, Any]:
    """
    Computes statistical aggregates for a list of amounts.
    """
    if not amounts:
        return {
            "total_spend": 0.0,
            "average_spend": 0.0,
            "median_spend": 0.0,
            "mode_spend": []
        }
    
    total = sum(amounts)
    mean = statistics.mean(amounts)
    
    # Median requires at least one element
    median = statistics.median(amounts) if amounts else 0.0
    
    # Mode might raise StatisticsError if no unique mode (e.g., all values are unique)
    # Or if there are multiple modes.
    try:
        mode = statistics.multimode(amounts) # Returns a list of modes
    except statistics.StatisticsError:
        mode = [] # No unique mode found

    return {
        "total_spend": round(total, 2),
        "average_spend": round(mean, 2),
        "median_spend": round(median, 2),
        "mode_spend": [round(m, 2) for m in mode] # Round modes as well
    }

def get_vendor_frequency(vendors: List[str]) -> Dict[str, int]:
    """
    Calculates the frequency distribution (histogram) of vendor occurrences.
    """
    # Filter out None or non-string vendors before counting
    valid_vendors = [v for v in vendors if isinstance(v, str) and v.strip()]
    return dict(Counter(valid_vendors))

def get_monthly_spend(receipts_data: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculates monthly spend trends.
    Expects receipts_data to be a list of dicts with 'transaction_date' and 'amount'.
    Handles various date formats if they come as strings.
    """
    if not receipts_data:
        return {}

    # Filter out entries with missing or invalid date/amount
    valid_data = []
    for item in receipts_data:
        item_date = item.get('transaction_date')
        item_amount = item.get('amount')

        # Attempt to convert date to datetime object if it's a string
        if isinstance(item_date, str):
            try:
                item_date = datetime.strptime(item_date, "%Y-%m-%d")
            except ValueError:
                item_date = None # Cannot parse date string
        elif isinstance(item_date, date) and not isinstance(item_date, datetime):
            # Convert date object to datetime object for pandas
            item_date = datetime(item_date.year, item_date.month, item_date.day)


        if item_date and isinstance(item_date, datetime) and isinstance(item_amount, (int, float)):
            valid_data.append({"transaction_date": item_date, "amount": item_amount})
    
    if not valid_data:
        return {}

    # Convert to Pandas DataFrame for easy time-series operations
    df = pd.DataFrame(valid_data)
    
    # Set date as index and resample by month, then sum amounts
    # .dt.to_period('M') converts to 'YYYY-MM' period
    monthly_spend = df.set_index('transaction_date')['amount'].resample('M').sum()
    
    # Convert PeriodIndex to string for dictionary keys
    return {str(idx.to_period('M')): round(val, 2) for idx, val in monthly_spend.items()}

# Example Usage (for testing algorithms directly)
if __name__ == "__main__":
    sample_receipts = [
        {"id": 1, "vendor": "SuperMart", "transaction_date": date(2025, 1, 15), "amount": 150.75, "category": "Groceries"},
        {"id": 2, "vendor": "Cafe XYZ", "transaction_date": date(2025, 1, 20), "amount": 50.00, "category": "Restaurant"},
        {"id": 3, "vendor": "Bookworm", "transaction_date": date(2025, 2, 5), "amount": 200.00, "category": "Books"},
        {"id": 4, "vendor": "SuperMart", "transaction_date": date(2025, 2, 10), "amount": 120.50, "category": "Groceries"},
        {"id": 5, "vendor": "Cafe XYZ", "transaction_date": date(2025, 3, 1), "amount": 50.00, "category": "Restaurant"},
        {"id": 6, "vendor": "Online Store", "transaction_date": date(2025, 3, 15), "amount": 300.00, "category": "Electronics"},
        {"id": 7, "vendor": "SuperMart", "transaction_date": date(2025, 3, 20), "amount": 150.75, "category": "Groceries"},
        {"id": 8, "vendor": "Fitness Gym", "transaction_date": date(2025, 4, 1), "amount": 100.00, "category": "Health"},
        {"id": 9, "vendor": "Cafe XYZ", "transaction_date": date(2025, 4, 5), "amount": 50.00, "category": "Restaurant"},
        {"id": 10, "vendor": "NullVendor", "transaction_date": None, "amount": 75.00, "category": "Misc"}, # Test missing date
        {"id": 11, "vendor": "InvalidAmount", "transaction_date": date(2025, 5, 1), "amount": "invalid", "category": "Error"}, # Test invalid amount type
        {"id": 12, "vendor": "FutureShop", "transaction_date": date(2026, 1, 1), "amount": 10.00, "category": "Future"}, # Test future date
        {"id": 13, "vendor": "NoCategory", "transaction_date": date(2025, 6, 1), "amount": 25.00, "category": None}, # Test None category
    ]

    print("--- Search Test ---")
    search_results = perform_search(sample_receipts, vendor="super", start_date=date(2025, 2, 1), end_date=date(2025, 3, 31))
    print(f"Search Results (vendor 'super', Feb-Mar): {search_results}")
    
    search_results_invalid_date = perform_search(sample_receipts, start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
    print(f"Search Results (Jan 2025, including invalid date entry): {search_results_invalid_date}")


    print("\n--- Sort Test (Amount Desc) ---")
    sorted_by_amount = perform_sort(sample_receipts, "amount", "desc")
    print(f"Sorted by Amount (Desc): {sorted_by_amount}")
    
    print("\n--- Sort Test (Vendor Asc) ---")
    sorted_by_vendor = perform_sort(sample_receipts, "vendor", "asc")
    print(f"Sorted by Vendor (Asc): {sorted_by_vendor}")

    print("\n--- Aggregates Test ---")
    amounts_list = [r["amount"] for r in sample_receipts if isinstance(r["amount"], (int, float))] # Filter out invalid amounts for aggregation
    aggregates = calculate_aggregates(amounts_list)
    print(f"Aggregates: {aggregates}")

    print("\n--- Vendor Frequency Test ---")
    vendors_list = [r["vendor"] for r in sample_receipts]
    vendor_freq = get_vendor_frequency(vendors_list)
    print(f"Vendor Frequency: {vendor_freq}")

    print("\n--- Monthly Spend Test ---")
    monthly_spend_data = get_monthly_spend(sample_receipts)
    print(f"Monthly Spend: {monthly_spend_data}")

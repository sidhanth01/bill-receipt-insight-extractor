# frontend/app.py

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import date, datetime
from typing import Dict, Any, List, Optional
import urllib.parse # Added for URL encoding
import os

# --- Custom CSS for UI Styling ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

/* General Body and Font Styling */
html, body, [class*="st-emotion"] {
    font-family: 'Inter', sans-serif;
    color: #333333; /* Dark grey text for readability */
    background-color: #f0f2f6; /* Light grey background */
}

/* Main Title Styling */
h1 {
    color: #2E8B57; /* Sea Green - a financial/growth color */
    text-align: center;
    font-weight: 700;
    font-size: 2.5rem; /* Larger title */
    margin-bottom: 0.5em;
}

/* Subheader/Markdown Styling (for descriptions) */
.stMarkdown p {
    font-size: 1.1rem;
    color: #555555;
    text-align: center;
    margin-bottom: 2em;
}

/* Button Styling */
.stButton>button {
    background-color: #4CAF50; /* Green */
    color: white;
    border-radius: 12px; /* More rounded corners */
    border: none;
    padding: 12px 28px; /* More padding */
    font-size: 1.1rem; /* Larger font */
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 4px 10px 0 rgba(0,0,0,0.2); /* Soft shadow */
    transition: all 0.3s ease; /* Smooth transition on hover */
    display: block; /* Make button take full width of its column */
    margin: 15px auto; /* Center button */
}
.stButton>button:hover {
    background-color: #45a049; /* Darker green on hover */
    box-shadow: 0 8px 16px 0 rgba(0,0,0,0.25); /* More pronounced shadow on hover */
    transform: translateY(-2px); /* Slight lift effect */
}

/* File Uploader Styling */
.stFileUploader {
    border: 2px dashed #a0a0a0; /* Dashed border */
    border-radius: 12px;
    padding: 20px;
    background-color: #ffffff; /* White background */
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

/* Tabs Styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 15px; /* Space between tabs */
    justify-content: center; /* Center the tabs */
    margin-bottom: 20px;
}
.stTabs [data-baseweb="tab-list"] button {
    background-color: #e0e0e0; /* Light grey for inactive tabs */
    color: #555555; /* Darker text for inactive tabs */
    border-radius: 10px 10px 0 0; /* Rounded top corners */
    padding: 10px 25px;
    font-size: 1.1rem;
    font-weight: 600;
    border: none;
    transition: all 0.3s ease;
}
.stTabs [aria-selected="true"] {
    background-color: #ffffff !important; /* White background for active tab */
    color: #2E8B57 !important; /* Sea Green for active tab text */
    border-bottom: 3px solid #2E8B57 !important; /* Green underline for active tab */
    box-shadow: 0 -2px 5px rgba(0,0,0,0.1); /* Subtle shadow on active tab */
}

/* Dataframe Styling (st.dataframe) */
.stDataFrame {
    border-radius: 12px;
    overflow: hidden; /* Ensures rounded corners apply to content */
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

/* Metric Cards (st.metric) */
[data-testid="stMetric"] {
    background-color: #ffffff;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    border-left: 5px solid #4CAF50; /* Green border on left */
}
[data-testid="stMetricLabel"] {
    font-size: 1.1rem;
    color: #555555;
}
[data-testid="stMetricValue"] {
    font-size: 2.2rem;
    color: #2E8B57; /* Sea Green */
    font-weight: 700;
}

/* Warning/Info Messages */
.stAlert {
    border-radius: 8px;
}

/* Expander (st.expander) - if used */
.stExpander {
    border-radius: 12px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    background-color: #ffffff;
    padding: 10px;
}

/* General Input Fields */
.stTextInput>div>div>input, .stNumberInput>div>div>input {
    border-radius: 8px;
    border: 1px solid #cccccc;
    padding: 8px 12px;
}
.stSelectbox>div>div {
    border-radius: 8px;
    border: 1px solid #cccccc;
}

</style>
""", unsafe_allow_html=True)

# --- End Custom CSS ---

# Define the backend API URL
BACKEND_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

st.set_page_config(layout="wide", page_title="Bill & Receipt Insight Extractor")

st.title("💸 Bill & Receipt Insight Extractor")
st.markdown("Upload your receipts and bills to extract data and gain financial insights!")

# --- Helper Functions for API Calls ---
def upload_file_to_backend(uploaded_file):
    """Sends the uploaded file to the FastAPI backend."""
    if uploaded_file is None:
        return None # No file uploaded

    if BACKEND_URL == "http://localhost:8000":
        st.error("Error: Backend URL is still set to localhost. Please ensure BACKEND_API_URL secret is correctly configured in Streamlit Cloud.")
        return None

    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
    response = None # Initialize response to None to prevent UnboundLocalError
    try:
        response = requests.post(f"{BACKEND_URL}/upload-receipt/", files=files)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error uploading file to backend: {e}")
        if response is not None:
            st.error(f"Backend response status: {response.status_code}")
            st.error(f"Backend response detail: {response.text}")
        else:
            st.error("Could not connect to the backend API. Check URL and network.")
        return None

def fetch_receipts(
    vendor: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 500 # Ensure this matches backend limit
) -> Optional[List[Dict[str, Any]]]:
    """Fetches receipts from the backend with optional filters."""
    if BACKEND_URL == "http://localhost:8000":
        st.error("Error: Backend URL is still set to localhost. Please ensure BACKEND_API_URL secret is correctly configured in Streamlit Cloud.")
        return None

    params = {
        "skip": skip,
        "limit": limit
    }
    if vendor: params["vendor"] = vendor
    if start_date: params["start_date"] = start_date.isoformat()
    if end_date: params["end_date"] = end_date.isoformat()
    if min_amount is not None: params["min_amount"] = min_amount
    if max_amount is not None: params["max_amount"] = max_amount
    if category: params["category"] = category

    response = None # Initialize response to None
    try:
        response = requests.get(f"{BACKEND_URL}/receipts/", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching receipts: {e}")
        if response is not None:
            st.error(f"Backend response status: {response.status_code}")
            st.error(f"Backend response detail: {response.text}")
        else:
            st.error("Could not connect to the backend API. Check URL and network.")
        return None

def update_receipt_in_backend(receipt_id: int, update_data: Dict[str, Any]):
    """Updates a receipt in the backend."""
    try:
        response = requests.put(f"{BACKEND_URL}/receipts/{receipt_id}", json=update_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error updating receipt: {e}")
        if response is not None:
            st.error(f"Backend response: {response.status_code} - {response.text}")
        return None

def delete_receipt_from_backend(receipt_id: int):
    """Deletes a receipt from the backend."""
    try:
        response = requests.delete(f"{BACKEND_URL}/receipts/{receipt_id}")
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Error deleting receipt: {e}")
        if response is not None:
            st.error(f"Backend response: {response.status_code} - {response.text}")
        return False

def fetch_aggregates():
    """Fetches aggregate statistics from the backend."""
    try:
        response = requests.get(f"{BACKEND_URL}/receipts/aggregates/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching aggregates: {e}")
        return None

def fetch_vendor_frequency():
    """Fetches vendor frequency from the backend."""
    try:
        response = requests.get(f"{BACKEND_URL}/receipts/vendor-frequency/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching vendor frequency: {e}")
        return None

def fetch_monthly_spend():
    """Fetches monthly spend from the backend."""
    try:
        response = requests.get(f"{BACKEND_URL}/receipts/monthly-spend/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching monthly spend: {e}")
        return None

# --- UI Layout ---
tab1, tab2, tab3 = st.tabs(["Upload & View Receipts", "Insights & Visualizations", "Admin (Manual Correction)"])

with tab1:
    st.header("Upload New Receipt/Bill")
    uploaded_file = st.file_uploader(
        "Choose a file (JPG, PNG, PDF, TXT)",
        type=["jpg", "jpeg", "png", "pdf", "txt"],
        accept_multiple_files=False
    )

    if uploaded_file:
        if st.button("Process & Save Receipt"):
            with st.spinner("Processing file..."):
                result = upload_file_to_backend(uploaded_file)
                if result:
                    st.success(result["message"])
                    if result["parsed_data"]:
                        st.subheader("Parsed Data:")
                        st.json(result["parsed_data"])
                    # Removed st.session_state.refresh_receipts = True here.
                    # Rely on Streamlit's natural rerun or explicit button for refresh.
                else:
                    st.error("Failed to process receipt. Check logs for details.")
    
    st.markdown("---")
    st.header("View All Receipts")

    # Filters for viewing receipts
    col1, col2, col3 = st.columns(3)
    with col1:
        search_vendor = st.text_input("Search by Vendor (partial match)")
    with col2:
        search_category = st.text_input("Search by Category (partial match)")
    with col3:
        date_range = st.date_input("Filter by Date Range", value=(), key="date_range_filter") # Corrected value to None
        start_date_filter = date_range[0] if date_range and len(date_range) > 0 else None
        end_date_filter = date_range[1] if date_range and len(date_range) > 1 else None
    
    col4, col5 = st.columns(2)
    with col4:
        min_amount_filter = st.number_input("Min Amount", min_value=0.0, value=None, format="%.2f")
    with col5:
        max_amount_filter = st.number_input("Max Amount", min_value=0.0, value=None, format="%.2f")

    # Sorting options
    sort_col, sort_dir_col = st.columns(2)
    with sort_col:
        # Use a key to ensure this widget's state is distinct if it appears multiple times
        sort_by = st.selectbox("Sort by", ["transaction_date", "amount", "vendor", "category"], key="sort_by_main")
    with sort_dir_col:
        # Use a key for the radio button too
        sort_direction = st.radio("Direction", ["asc", "desc"], horizontal=True, key="sort_direction_main")

    # --- Data Fetching and Sorting Logic ---
    # Fetch receipts whenever filter inputs change (Streamlit's default behavior)
    # Use st.session_state to store the raw fetched data to avoid re-fetching on sort changes
    
    # Define a unique key for the fetched data in session state
    FETCHED_RECEIPTS_KEY = "fetched_receipts_data"

    # Only fetch if filters change OR if data is not already in session state
    # We use a hash of filter parameters to detect changes
    current_filter_params = (
        search_vendor, start_date_filter, end_date_filter,
        min_amount_filter, max_amount_filter, search_category
    )
    
    if FETCHED_RECEIPTS_KEY not in st.session_state or \
       st.session_state.get(f"{FETCHED_RECEIPTS_KEY}_filters") != current_filter_params:
        with st.spinner("Fetching receipts..."):
            receipts_data = fetch_receipts(
                vendor=search_vendor,
                start_date=start_date_filter,
                end_date=end_date_filter,
                min_amount=min_amount_filter,
                max_amount=max_amount_filter,
                category=search_category
            )
            if receipts_data:
                # Convert to DataFrame and store in session state
                df_receipts_raw = pd.DataFrame(receipts_data)
                if 'transaction_date' in df_receipts_raw.columns:
                    df_receipts_raw['transaction_date'] = pd.to_datetime(df_receipts_raw['transaction_date'])
                
                # FIX: Ensure 'amount' column is numeric, coercing errors to NaN
                if 'amount' in df_receipts_raw.columns:
                    df_receipts_raw['amount'] = pd.to_numeric(df_receipts_raw['amount'], errors='coerce')

                st.session_state[FETCHED_RECEIPTS_KEY] = df_receipts_raw
            else:
                st.session_state[FETCHED_RECEIPTS_KEY] = pd.DataFrame() # Store empty DataFrame
                st.warning("Could not retrieve receipts from the backend or no matches found.")
        st.session_state[f"{FETCHED_RECEIPTS_KEY}_filters"] = current_filter_params
    
    # Always apply sorting to the DataFrame stored in session state
    df_display = st.session_state.get(FETCHED_RECEIPTS_KEY)

    if not df_display.empty:
        # Determine sort keys and ascending order
        sort_keys = [sort_by]
        ascending_orders = [(sort_direction == "asc")]

        # If sorting by date, add a secondary sort by amount (ascending) for consistency
        if sort_by == "transaction_date":
            sort_keys.append("amount")
            ascending_orders.append(True) # Sort amount ascending for same dates

        # Apply in-memory sorting based on user selection
        df_display = df_display.sort_values(
            by=sort_keys,
            ascending=ascending_orders,
            na_position='last' # Puts None/NaN values at the end
        )
        st.dataframe(df_display.drop(columns=['id']), use_container_width=True) # Drop ID for display
    elif st.session_state.get(f"{FETCHED_RECEIPTS_KEY}_filters") is not None: # Only show info if filters were applied
        st.info("No receipts found matching the criteria.")

    # --- Export Buttons ---
    st.markdown("---")
    st.subheader("Export Current View")
    export_cols = st.columns(2)

    with export_cols[0]:
        # Generate the CSV download link
        # We need to construct the URL for the backend's CSV export endpoint
        # The filters from the current view should be passed as query parameters
        csv_export_url_params = {
            "vendor": search_vendor,
            "start_date": start_date_filter.isoformat() if start_date_filter else None,
            "end_date": end_date_filter.isoformat() if end_date_filter else None,
            "min_amount": min_amount_filter,
            "max_amount": max_amount_filter,
            "category": search_category
        }
        # Filter out None values from params to avoid sending them in URL
        csv_export_params_cleaned = {k: v for k, v in csv_export_url_params.items() if v is not None}
        
        # Construct the full URL with query parameters
        import urllib.parse
        query_string = urllib.parse.urlencode(csv_export_params_cleaned)
        csv_download_url = f"{BACKEND_URL}/export/csv/?{query_string}"

        st.download_button(
            label="Download as CSV",
            data=requests.get(csv_download_url).content, # Fetch data from backend
            file_name="receipts_export.csv",
            mime="text/csv",
            help="Download the currently filtered receipts as a CSV file."
        )

    with export_cols[1]:
        # Generate the JSON download link
        json_export_url_params = {
            "vendor": search_vendor,
            "start_date": start_date_filter.isoformat() if start_date_filter else None,
            "end_date": end_date_filter.isoformat() if end_date_filter else None,
            "min_amount": min_amount_filter,
            "max_amount": max_amount_filter,
            "category": search_category
        }
        json_export_params_cleaned = {k: v for k, v in json_export_url_params.items() if v is not None}
        query_string_json = urllib.parse.urlencode(json_export_params_cleaned)
        json_download_url = f"{BACKEND_URL}/export/json/?{query_string_json}"

        st.download_button(
            label="Download as JSON",
            data=requests.get(json_download_url).content, # Fetch data from backend
            file_name="receipts_export.json",
            mime="application/json",
            help="Download the currently filtered receipts as a JSON file."
        )


with tab2:
    st.header("Financial Insights & Visualizations")

    # --- Aggregates ---
    st.subheader("Overall Expenditure Statistics")
    aggregates = fetch_aggregates()
    if aggregates:
        col_agg1, col_agg2, col_agg3, col_agg4 = st.columns(4)
        col_agg1.metric("Total Spend", f"₹{aggregates['total_spend']:.2f}")
        col_agg2.metric("Average Spend", f"₹{aggregates['average_spend']:.2f}")
        col_agg3.metric("Median Spend", f"₹{aggregates['median_spend']:.2f}")
        col_agg4.metric("Mode Spend", f"₹{', '.join([f'{m:.2f}' for m in aggregates['mode_spend']])}")
    else:
        st.info("No data available to calculate aggregates.")

    st.markdown("---")

    # --- Vendor Frequency ---
    st.subheader("Vendor Distribution")
    vendor_freq = fetch_vendor_frequency()
    if vendor_freq:
        df_vendor_freq = pd.DataFrame(list(vendor_freq.items()), columns=['Vendor', 'Count'])
        fig_vendor = px.bar(
            df_vendor_freq.sort_values(by='Count', ascending=False),
            x='Vendor',
            y='Count',
            title='Number of Receipts per Vendor',
            labels={'Vendor': 'Vendor Name', 'Count': 'Number of Receipts'}
        )
        st.plotly_chart(fig_vendor, use_container_width=True)
    else:
        st.info("No vendor data available for distribution.")

    st.markdown("---")

    # --- Category Distribution ---
    st.subheader("Category Distribution")
    # Fetch all receipts to calculate category distribution on frontend
    all_receipts_for_category = fetch_receipts(limit=500) # Fetch a large limit (within backend's max)
    if all_receipts_for_category:
        df_categories = pd.DataFrame(all_receipts_for_category)
        if not df_categories.empty and 'category' in df_categories.columns:
            category_counts = df_categories['category'].value_counts().reset_index()
            category_counts.columns = ['Category', 'Count']
            fig_category = px.pie(
                category_counts,
                values='Count',
                names='Category',
                title='Receipts by Category',
                hole=0.3 # Creates a donut chart
            )
            st.plotly_chart(fig_category, use_container_width=True)
        else:
            st.info("No category data available for distribution.")
    else:
        st.info("No receipts data available for category distribution.")

    st.markdown("---")

    # --- Monthly Spend Trend ---
    st.subheader("Monthly Spend Trend")
    monthly_spend = fetch_monthly_spend()
    if monthly_spend:
        # Convert dictionary to DataFrame for Plotly
        df_monthly_spend = pd.DataFrame(list(monthly_spend.items()), columns=['Month', 'Spend'])
        df_monthly_spend['Month'] = pd.to_datetime(df_monthly_spend['Month']) # Convert to datetime for proper sorting
        df_monthly_spend = df_monthly_spend.sort_values(by='Month') # Ensure chronological order

        fig_monthly = px.line(
            df_monthly_spend,
            x='Month',
            y='Spend',
            title='Monthly Expenditure Trend',
            markers=True # Show points on the line
        )
        fig_monthly.update_xaxes(dtick="M1", tickformat="%b\n%Y") # Format x-axis for months
        st.plotly_chart(fig_monthly, use_container_width=True)
    else:
        st.info("No monthly spend data available.")

with tab3:
    st.header("Admin Panel: Manual Correction & Deletion")
    st.warning("Use this panel with caution. Changes are permanent.")

    # Fetch all receipts for selection
    all_receipts_for_admin = fetch_receipts(limit=500) # Fetch a large limit (within backend's max)
    if all_receipts_for_admin:
        df_admin_receipts = pd.DataFrame(all_receipts_for_admin)
        df_admin_receipts['display_name'] = df_admin_receipts.apply(
            lambda row: f"{row['vendor']} - {row['transaction_date']} - ₹{row['amount']:.2f} (ID: {row['id']})", axis=1
        )
        
        selected_receipt_display = st.selectbox(
            "Select Receipt to Edit/Delete",
            df_admin_receipts['display_name'].tolist() if not df_admin_receipts.empty else []
        )

        if selected_receipt_display:
            selected_receipt_id = df_admin_receipts[
                df_admin_receipts['display_name'] == selected_receipt_display
            ]['id'].iloc[0]
            
            current_receipt_data = df_admin_receipts[
                df_admin_receipts['id'] == selected_receipt_id
            ].iloc[0].to_dict()

            st.subheader(f"Editing Receipt ID: {selected_receipt_id}")
            
            with st.form(key=f"edit_form_{selected_receipt_id}"):
                new_vendor = st.text_input("Vendor", value=current_receipt_data.get('vendor', ''))
                new_date = st.date_input("Transaction Date", value=pd.to_datetime(current_receipt_data.get('transaction_date', date.today())))
                new_amount = st.number_input("Amount", value=float(current_receipt_data.get('amount', 0.0)), format="%.2f")
                new_category = st.text_input("Category", value=current_receipt_data.get('category', ''))

                submit_update = st.form_submit_button("Update Receipt")

                if submit_update:
                    update_payload = {
                        "vendor": new_vendor,
                        "transaction_date": new_date.isoformat(), # Convert date object to ISO format string
                        "amount": new_amount,
                        "category": new_category
                    }
                    with st.spinner("Updating receipt..."):
                        updated_data = update_receipt_in_backend(selected_receipt_id, update_payload)
                        if updated_data:
                            st.success(f"Receipt ID {selected_receipt_id} updated successfully!")
                            st.json(updated_data)
                            st.session_state.refresh_receipts = True # Trigger refresh
                        else:
                            st.error(f"Failed to update receipt ID {selected_receipt_id}.")
            
            st.markdown("---")
            st.subheader(f"Delete Receipt ID: {selected_receipt_id}")
            if st.button(f"Delete Receipt {selected_receipt_id}", key=f"delete_btn_{selected_receipt_id}"):
                # Streamlit's warning message doesn't block execution, so we need a separate confirm button
                st.warning(f"Are you sure you want to delete receipt ID {selected_receipt_id}? This action is irreversible.")
                if st.button("Confirm Delete", key=f"confirm_delete_btn_{selected_receipt_id}"):
                    with st.spinner("Deleting receipt..."):
                        if delete_receipt_from_backend(selected_receipt_id):
                            st.success(f"Receipt ID {selected_receipt_id} deleted successfully.")
                            # To clear the selectbox and refresh the list, we can trigger a rerun
                            # by setting a flag or using st.experimental_rerun()
                            st.session_state.refresh_receipts = True # This will trigger a re-fetch on next run
                            # For immediate clear, you might need a more complex state management
                        else:
                            st.error(f"Failed to delete receipt ID {selected_receipt_id}.")
        # This else block ensures the selectbox is cleared if the item was just deleted
        if st.session_state.get('refresh_receipts', False): # Check if a refresh was requested
            st.session_state.refresh_receipts = False # Reset the flag
            st.rerun() # Changed from st.experimental_rerun()
    else:
        st.info("No receipts available for administration.")

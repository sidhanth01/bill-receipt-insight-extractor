# backend/core/parser.py

import re
from datetime import datetime
from typing import Dict, Any, Optional
from PIL import Image
import pytesseract
from PyPDF2 import PdfReader
import io

# IMPORTANT: If Tesseract is not found, uncomment and set the path to your tesseract.exe
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# For Linux/macOS, it's usually in PATH, but if not, you might need to specify the full path
# pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract' # Example for macOS Homebrew

class ReceiptParser:
    """
    A class to parse structured data from various receipt/bill file formats.
    Supports TXT, PDF, JPG, PNG.
    """
    def __init__(self):
        # Define common regex patterns for extraction
        self.patterns = {
            # Amount: Looks for keywords like Total, Amount, etc., followed by optional currency
            # and then a number (handles commas and decimals).
            "amount": r"(?:Total|Amount|Balance Due|Grand Total|Net Payable|Payable|Sum)\s*[:]?\s*[\$€£₹]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            
            # Date: Matches various common date formats (DD-MM-YYYY, YYYY-MM-DD, Month DD, YYYY)
            "date": r"\b(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})\b|\b(\d{4}[-/.]\d{1,2}[-/.]\d{1,2})\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b",
            
            # Vendor: Improved patterns for vendor extraction
            # 1. Look for common introductory phrases
            # 2. Look for lines that seem like a company name (e.g., all caps, prominent)
            # 3. Capture text after "To:" or "From:"
            "vendor_patterns": [
                r"(?:Invoice from|Bill from|Purchased at|Sold by|Store|Shop|Vendor|From)\s*[:]?\s*([A-Za-z0-9\s.&'-]+)",
                r"^(?!Date|Total|Amount|Invoice|Bill|Receipt|Items|Subtotal|Tax)\s*([A-Z0-9\s.&'-]+?)\s*$", # Capture prominent lines (e.g., all caps) at start of line
                r"To:\s*([A-Za-z0-9\s.&'-]+)", # For "To:"
                r"From:\s*([A-Za-z0-9\s.&'-]+)", # For "From:"
                r"^(?:\s*)\s*([A-Za-z0-9\s.&'-]+?)\s*$", # Generic capture of first non-empty line
            ],
            
            # Category Keywords: Simple keyword mapping for categorization
            "category_keywords": {
                "electronics": ["electronics", "tech", "gadget", "computer", "mobile", "device"], # Added Electronics category, placed higher
                "groceries": ["supermarket", "mart", "grocery", "fresh", "food", "hyper", "provision"],
                "utilities": ["electricity", "internet", "water", "gas", "power", "telecom", "broadband"],
                "transport": ["fuel", "petrol", "cab", "taxi", "bus", "metro", "auto"], # Removed "travel" for less ambiguity
                "restaurant": ["restaurant", "cafe", "diner", "eatery", "hotel", "food", "dine"],
                "pharmacy": ["pharmacy", "chemist", "medicine", "health", "drug"],
                "clothing": ["fashion", "apparel", "boutique", "garment", "wear"],
                "entertainment": ["movie", "cinema", "theatre", "park", "amusement", "gaming"],
                "rent": ["rent", "landlord", "housing", "apartment"],
                "education": ["school", "college", "university", "course", "tuition", "academy"],
                "healthcare": ["hospital", "clinic", "doctor", "medical"],
                "personal care": ["salon", "spa", "barber", "beauty"],
                "books": ["book", "bookstore", "library", "novel", "reading"] # Added Books category
            }
        }

    def _extract_text_from_image(self, image_bytes: bytes) -> str:
        """Extracts text from an image using Tesseract OCR."""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            # Convert to grayscale for better OCR performance
            image = image.convert('L')
            # You can also try enhancing contrast or resizing for better OCR
            # image = image.resize((image.width * 2, image.height * 2), Image.LANCZOS)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            print(f"Error extracting text from image: {e}")
            return ""

    def _extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """Extracts text from a PDF file."""
        text = ""
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                text += page.extract_text() or "" # extract_text() can return None
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""

    def _parse_text(self, text: str) -> Dict[str, Any]:
        """Parses extracted text to find structured data using regex and rule-based logic."""
        parsed_data = {
            "vendor": "Unknown",
            "transaction_date": None,
            "amount": None,
            "category": "Uncategorized"
        }

        # Normalize text for easier parsing (e.g., lowercase for keyword matching)
        normalized_text = text.lower().strip()

        # --- Extract Amount ---
        amount_match = re.search(self.patterns["amount"], text, re.IGNORECASE)
        if amount_match:
            # Remove commas if present (e.g., 1,234.56 -> 1234.56)
            amount_str = amount_match.group(1).replace(',', '')
            try:
                parsed_data["amount"] = float(amount_str)
            except ValueError:
                pass # Keep as None if conversion fails

        # --- Extract Date ---
        # Prioritize YYYY-MM-DD as it's unambiguous for datetime.strptime
        date_formats = [
            "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", # YYYY-MM-DD
            "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", # DD-MM-YYYY
            "%d-%m-%y", "%d/%m/%y", "%d.%m.%y", # DD-MM-YY (e.g., 25-07-24 for 2024)
            "%b %d, %Y", "%B %d, %Y", # Mon DD, YYYY (e.g., Jul 19, 2025)
            "%d %b %Y", "%d %B %Y" # DD Mon YYYY
        ]
        date_match = re.search(self.patterns["date"], text, re.IGNORECASE)
        if date_match:
            date_str = date_match.group(0) # Get the full matched string
            for fmt in date_formats:
                try:
                    # Using datetime.strptime and then .date() to get just the date part
                    parsed_data["transaction_date"] = datetime.strptime(date_str, fmt).date()
                    break # Found a valid date, stop trying formats
                except ValueError:
                    continue # Try next format
        
        # --- Extract Vendor (Improved Logic) ---
        # Try multiple vendor patterns sequentially
        for pattern in self.patterns["vendor_patterns"]:
            vendor_match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if vendor_match:
                vendor_name = vendor_match.group(1).strip()
                # Clean up common trailing characters or phrases from vendor name
                vendor_name = re.sub(r'(?:invoice|bill|receipt|store|shop|vendor|from|at|date|total|amount|items)\s*[:]?\s*$', '', vendor_name, flags=re.IGNORECASE).strip()
                # Remove any leading/trailing non-alphanumeric characters except spaces and common symbols
                vendor_name = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', vendor_name).strip()
                if vendor_name: # Only assign if not empty after cleaning
                    parsed_data["vendor"] = vendor_name.title() # Capitalize first letter of each word for consistency
                    break # Found a vendor, stop trying other patterns

        # Fallback: If no vendor found by patterns, try to get the first non-empty line
        if parsed_data["vendor"] == "Unknown":
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            if lines:
                # Attempt to pick the first line that doesn't look like a date or amount
                for line in lines:
                    if not re.search(self.patterns["date"], line) and \
                       not re.search(self.patterns["amount"], line) and \
                       len(line) > 5 and len(line) < 50: # Simple length heuristic
                        parsed_data["vendor"] = line.title()
                        break


        # --- Infer Category based on keywords ---
        for category, keywords in self.patterns["category_keywords"].items():
            for keyword in keywords:
                if keyword in normalized_text:
                    parsed_data["category"] = category.capitalize()
                    break # Found a category, no need to check other keywords for this category
            if parsed_data["category"] != "Uncategorized":
                break # Found a category, no need to check other categories

        return parsed_data

    def parse_file(self, file_bytes: bytes, file_extension: str) -> Dict[str, Any]:
        """
        Parses the content of an uploaded file based on its extension.
        Returns a dictionary of extracted fields.
        """
        extracted_text = ""
        if file_extension in [".jpg", ".png", ".jpeg"]:
            extracted_text = self._extract_text_from_image(file_bytes)
        elif file_extension == ".pdf":
            extracted_text = self._extract_text_from_pdf(file_bytes)
        elif file_extension == ".txt":
            # Assuming UTF-8 encoding for text files
            try:
                extracted_text = file_bytes.decode('utf-8')
            except UnicodeDecodeError:
                # Fallback to a common encoding if UTF-8 fails
                extracted_text = file_bytes.decode('latin-1', errors='ignore')
        else:
            raise ValueError(f"Unsupported file type: {file_extension}. Allowed: JPG, PNG, PDF, TXT.")

        if not extracted_text.strip(): # Check if extracted text is empty or just whitespace
            raise ValueError("Could not extract any meaningful text from the provided file.")

        parsed_data = self._parse_text(extracted_text)
        return parsed_data

# Example Usage (for testing parser logic directly)
# This block will ONLY run when parser.py is executed directly, not when imported.
if __name__ == "__main__":
    parser = ReceiptParser() # This line is now correctly inside the if __name__ == "__main__": block

    # --- Test with a dummy text file content ---
    print("\n--- Testing with TXT content (Global Supermart) ---")
    # Changed from byte literal to regular string and then encode
    txt_content_gsm_str = """
    ----------------------------------------------------
               GLOBAL SUPERMART
    ----------------------------------------------------
    Date: 2025-07-20
    Invoice No: GSM-2025-07-001
    Customer: Sidhanth

    Items:
    - Organic Milk (1L)        @ ₹ 75.50
    - Fresh Bread (1 pc)       @ ₹ 40.00
    - Assorted Vegetables      @ ₹ 120.75
    - Snacks (2 packs)         @ ₹ 80.00
    - Cleaning Supplies        @ ₹ 150.00

    Subtotal: ₹ 466.25
    Tax (5%): ₹ 23.31
    ----------------------------------------------------
    TOTAL AMOUNT: ₹ 489.56
    ----------------------------------------------------
    Thank you for your groceries purchase!
    Visit us again!
    """
    try:
        # Encode the string to bytes before passing to parse_file
        parsed_txt_gsm = parser.parse_file(txt_content_gsm_str.encode('utf-8'), ".txt")
        print(f"Parsed TXT (Global Supermart): {parsed_txt_gsm}")
    except ValueError as e:
        print(f"Error parsing TXT (Global Supermart): {e}")

    print("\n--- Testing with TXT content (Daily Brew Cafe) ---")
    txt_content_dbc_str = """
    ----------------------------------------------------
                   DAILY BREW CAFE
    ----------------------------------------------------
    Date: 2025-07-21
    Order ID: DB-2025-07-005

    Items:
    - Latte (Large)            @ ₹ 200.00
    - Croissant                @ ₹ 120.00
    - Espresso (Double)        @ ₹ 180.00

    Total Payable: ₹ 500.00
    ----------------------------------------------------
    Enjoy your coffee!
    """
    try:
        parsed_txt_dbc = parser.parse_file(txt_content_dbc_str.encode('utf-8'), ".txt")
        print(f"Parsed TXT (Daily Brew Cafe): {parsed_txt_dbc}")
    except ValueError as e:
        print(f"Error parsing TXT (Daily Brew Cafe): {e}")

    print("\n--- Testing with TXT content (Tech Gadgets) ---")
    txt_content_tg_str = """
    ----------------------------------------------------
               TECH GADGETS INDIA
    ----------------------------------------------------
    Date: 2025-07-22
    Invoice: TG-2025-07-010
    Customer: Sidhanth

    Items:
    - USB-C Cable (2m)         @ ₹ 350.00
    - Wireless Mouse           @ ₹ 899.00
    - Screen Protector         @ ₹ 250.00

    Subtotal: ₹ 1499.00
    GST (18%): ₹ 269.82
    ----------------------------------------------------
    TOTAL AMOUNT: ₹ 1768.82
    ----------------------------------------------------
    Your trusted electronics partner.
    """
    try:
        parsed_txt_tg = parser.parse_file(txt_content_tg_str.encode('utf-8'), ".txt")
        print(f"Parsed TXT (Tech Gadgets): {parsed_txt_tg}")
    except ValueError as e:
        print(f"Error parsing TXT (Tech Gadgets): {e}")

    print("\n--- Testing with TXT content (no amount/date/vendor keywords) ---")
    txt_content_no_data_str = """
    Random Store Name
    123 Main Street
    City, State 12345
    (555) 123-4567

    Some random text.
    No structured data here.
    """
    try:
        parsed_no_data = parser.parse_file(txt_content_no_data_str.encode('utf-8'), ".txt")
        print(f"Parsed No Data: {parsed_no_data}")
    except ValueError as e:
        print(f"Error parsing No Data: {e}")

    # --- Test with a dummy image file (requires a local image file for real test) ---
    # For a real test, you would load an image file:
    # with open("path/to/your/receipt.png", "rb") as f:
    #     image_bytes = f.read()
    # try:
    #     parsed_image = parser.parse_file(image_bytes, ".png")
    #     print(f"Parsed Image: {parsed_image}")
    # except ValueError as e:
    #     print(f"Error parsing Image: {e}")

    # --- Test with a dummy PDF file (requires a local PDF file for real test) ---
    # For a real test, you would load a PDF file:
    # with open("path/to/your/bill.pdf", "rb") as f:
    #     pdf_bytes = f.read()
    # try:
    #     parsed_pdf = parser.parse_file(pdf_bytes, ".pdf")
    #     print(f"Parsed PDF: {parsed_pdf}")
    # except ValueError as e:
    #     print(f"Error parsing PDF: {e}")

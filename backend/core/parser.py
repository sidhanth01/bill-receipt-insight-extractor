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
            # Amount: Robust regex to capture the number.
            # It now captures a digit, followed by any combination of digits, commas, or dots.
            "amount": r"(?:TOTAL\s*AMOUNT|TOTAL\s*DUE|AMOUNT\s*DUE|Balance\s*Due|Grand\s*Total|Net\s*Payable|Payable|Total|Amount|Sum|Bill)\s*[:=]?\s*[\$€£₹]?\s*(\d[\d,.]*)",
            
            # Date: Matches various common date formats (DD-MM-YYYY, YYYY-MM-DD, Month DD, YYYY)
            "date": r"\b(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})\b|\b(\d{4}[-/.]\d{1,2}[-/.]\d{1,2})\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b",
            
            # Vendor: Improved patterns for vendor extraction
            "vendor_patterns": [
                r"(?:Invoice from|Bill from|Purchased at|Sold by|Store|Shop|Vendor|From)\s*[:]?\s*([A-Za-z0-9\s.&'-]+)",
                r"^(?!Date|Total|Amount|Invoice|Bill|Receipt|Items|Subtotal|Tax)\s*([A-Z0-9\s.&'-]+?)\s*$",
                r"To:\s*([A-Za-z0-9\s.&'-]+)",
                r"From:\s*([A-Za-z0-9\s.&'-]+)",
                r"^(?:\s*)\s*([A-Za-z0-9\s.&'-]+?)\s*$",
            ],
            
            # Category Keywords: Simple keyword mapping for categorization
            "category_keywords": {
                "electronics": ["electronics", "tech", "gadget", "computer", "mobile", "device"],
                "groceries": ["supermarket", "mart", "grocery", "fresh", "food", "hyper", "provision"],
                "utilities": ["electricity", "internet", "water", "gas", "power", "telecom", "broadband", "bill"],
                "transport": ["fuel", "petrol", "cab", "taxi", "bus", "metro", "auto"],
                "restaurant": ["restaurant", "cafe", "diner", "eatery", "hotel", "food", "dine"],
                "pharmacy": ["pharmacy", "chemist", "medicine", "health", "drug"],
                "clothing": ["fashion", "apparel", "boutique", "garment", "wear"],
                "entertainment": ["movie", "cinema", "theatre", "park", "amusement", "gaming"],
                "rent": ["rent", "landlord", "housing", "apartment"],
                "education": ["school", "college", "university", "course", "tuition", "academy"],
                "healthcare": ["hospital", "clinic", "doctor", "medical"],
                "personal care": ["salon", "spa", "barber", "beauty"],
                "books": ["book", "bookstore", "library", "novel", "reading"]
            }
        }

    def _extract_text_from_image(self, image_bytes: bytes) -> str:
        """Extracts text from an image using Tesseract OCR."""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image = image.convert('L') # Grayscale for better OCR
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
                text += page.extract_text() or ""
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

        normalized_text = text.lower().strip()

        # --- Extract Amount ---
        amount_match = re.search(self.patterns["amount"], text, re.IGNORECASE)
        if amount_match:
            amount_str = amount_match.group(1)
            
            # --- SIMPLIFIED AND MORE ROBUST CLEANING LOGIC FOR AMOUNT_STR ---
            # Remove all characters that are NOT digits or a single dot (decimal separator).
            # This handles both comma and dot as thousands separators by simply removing them.
            # It then ensures only one decimal dot remains.

            # First, remove all commas (common thousands separator)
            cleaned_amount_str = amount_str.replace(',', '')
            
            # If there are multiple dots, assume all but the last are thousands separators
            # (e.g., 1.234.567,89 -> 1234567.89)
            if cleaned_amount_str.count('.') > 1:
                parts = cleaned_amount_str.split('.')
                # Join all parts except the last one (which is the decimal part)
                cleaned_amount_str = ''.join(parts[:-1]) + '.' + parts[-1]
            
            # Final safeguard: remove any non-digit/non-dot characters that might remain
            # This handles currency symbols that might have been captured inside the number string
            cleaned_amount_str = re.sub(r'[^\d.]', '', cleaned_amount_str)
            
            try:
                parsed_data["amount"] = float(cleaned_amount_str)
            except ValueError:
                pass # Keep as None if conversion fails

        # --- Extract Date ---
        date_formats = [
            "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d",
            "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y",
            "%d-%m-%y", "%d/%m/%y", "%d.%m.%y",
            "%b %d, %Y", "%B %d, %Y",
            "%d %b %Y", "%d %B %Y"
        ]
        date_match = re.search(self.patterns["date"], text, re.IGNORECASE)
        if date_match:
            date_str = date_match.group(0)
            for fmt in date_formats:
                try:
                    parsed_data["transaction_date"] = datetime.strptime(date_str, fmt).date()
                    break
                except ValueError:
                    continue
        
        # --- Extract Vendor (Improved Logic) ---
        for pattern in self.patterns["vendor_patterns"]:
            vendor_match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if vendor_match:
                vendor_name = vendor_match.group(1).strip()
                vendor_name = re.sub(r'(?:invoice|bill|receipt|store|shop|vendor|from|at|date|total|amount|items)\s*[:]?\s*$', '', vendor_name, flags=re.IGNORECASE).strip()
                vendor_name = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', vendor_name).strip()
                if vendor_name:
                    parsed_data["vendor"] = vendor_name.title()
                    break

        # Fallback: If no vendor found by patterns, try to get the first non-empty line
        if parsed_data["vendor"] == "Unknown":
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            if lines:
                for line in lines:
                    if not re.search(self.patterns["date"], line) and \
                       not re.search(self.patterns["amount"], line) and \
                       len(line) > 5 and len(line) < 50:
                        parsed_data["vendor"] = line.title()
                        break


        # --- Infer Category based on keywords ---
        for category, keywords in self.patterns["category_keywords"].items():
            for keyword in keywords:
                if keyword in normalized_text:
                    parsed_data["category"] = category.capitalize()
                    break
            if parsed_data["category"] != "Uncategorized":
                break

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
            try:
                extracted_text = file_bytes.decode('utf-8')
            except UnicodeDecodeError:
                extracted_text = file_bytes.decode('latin-1', errors='ignore')
        else:
            raise ValueError(f"Unsupported file type: {file_extension}. Allowed: JPG, PNG, PDF, TXT.")

        if not extracted_text.strip():
            raise ValueError("Could not extract any meaningful text from the provided file.")

        # --- Diagnostic Print ---
        print(f"\n--- Parser Diagnostic ---")
        print(f"File Extension: {file_extension}")
        print(f"Extracted Text:\n{extracted_text[:500]}...")
        
        parsed_data = self._parse_text(extracted_text)
        print(f"Parsed Data: {parsed_data}")
        print(f"--- End Diagnostic ---\n")

        return parsed_data

# Example Usage (for testing parser logic directly)
if __name__ == "__main__":
    parser = ReceiptParser()

    # --- Test with a dummy text file content ---
    print("\n--- Testing with TXT content (Global Supermart) ---")
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

    print("\n--- Testing with TXT content (Utility Bill) ---")
    txt_content_utility_str = """
    ----------------------------------------------------
               POWERGRID ELECTRICITY BOARD
    ----------------------------------------------------
    Bill Date: 2025-07-25
    Account No: 1234567890
    Billing Period: 2025-06-01 to 2025-06-30

    Previous Reading: 12345 kWh
    Current Reading:  12545 kWh
    Units Consumed:   200 kWh

    Charges:
    - Energy Charges: ₹ 1500.00
    - Fixed Charges:  ₹ 100.00
    - Surcharge:      ₹ 50.00

    Total Amount Due: ₹ 1650.00
    Due Date: 2025-08-10
    ----------------------------------------------------
    Thank you for your payment.
    """
    try:
        parsed_txt_utility = parser.parse_file(txt_content_utility_str.encode('utf-8'), ".txt")
        print(f"Parsed TXT (Utility Bill): {parsed_txt_utility}")
    except ValueError as e:
        print(f"Error parsing TXT (Utility Bill): {e}")

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

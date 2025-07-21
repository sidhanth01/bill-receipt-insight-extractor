# Bill & Receipt Insight Extractor

## Objective
A full-stack mini-application for uploading receipts and bills, extracting structured data, and presenting summarized insights.

## Technologies Used
* **Backend:** FastAPI, SQLModel, SQLite, pytesseract, Pillow, PyPDF2
* **Frontend:** Streamlit
* **Data Analysis:** Pandas, NumPy, Matplotlib, Plotly

## Setup Instructions

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/bill-receipt-insight-extractor.git](https://github.com/your-username/bill-receipt-insight-extractor.git)
    cd bill-receipt-insight-extractor
    ```
2.  **Set up Python Virtual Environment:**
    ```bash
    python -m venv venv
    # On Windows:
    # .\venv\Scripts\activate
    # On macOS/Linux:
    # source venv/bin/activate
    ```
3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Install Tesseract-OCR Engine (System-wide):**
    * **Windows:** Download from [Tesseract at UB Mannheim](https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-v5.3.0.20221222.exe). Ensure "Add to PATH" is checked.
    * **macOS:** `brew install tesseract`
    * **Linux (Debian/Ubuntu)::** `sudo apt install tesseract-ocr`
    * **Important:** After installing Tesseract, you might need to configure `pytesseract` if it's not found automatically. Add this line at the top of your `backend/core/parser.py` if needed (replace with your actual path):
        `pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'`

## How to Run

1.  **Start the Backend API:**
    ```bash
    cd backend
    uvicorn api.main:app --reload
    ```
2.  **Start the Frontend Dashboard:**
    ```bash
    cd frontend
    streamlit run app.py
# 💸 Bill & Receipt Insight Extractor

## ✨ Project Overview

A full-stack mini-application designed to streamline personal financial tracking by automating the extraction of structured data from various receipt and bill formats. It transforms raw financial documents into actionable insights, providing users with a clear overview of their spending habits through interactive visualizations and robust data management.

## 🎯 Project Objective

To develop a comprehensive solution that allows users to:
* **Upload** heterogeneous receipt/bill files (`.jpg`, `.png`, `.pdf`, `.txt`).
* **Extract** key financial data (Vendor, Date, Amount, Category) using a combination of OCR and rule-based parsing.
* **Store** this structured data in a reliable database.
* **Present** summarized insights and trends through an intuitive, interactive dashboard.
* **Enable** data management features like manual correction, deletion, and export.

## 📺 Demo

*(Once you create a 2-3 minute video or GIF demonstrating your project, you can embed it here. For now, this is a placeholder.)*

[![Watch the demo video](https://img.youtube.com/vi/YOUR_VIDEO_ID/0.jpg)](https://www.youtube.com/watch?v=YOUR_VIDEO_ID)
*(Replace `YOUR_VIDEO_ID` with your actual YouTube video ID)*

## 🚀 Key Features

* **Multi-Format File Ingestion:** Handles diverse receipt/bill formats including `.jpg`, `.png`, `.pdf`, and `.txt`.
* **Intelligent Data Parsing:** Extracts crucial structured data fields:
    * **Vendor / Biller:** Identifies the source of the transaction (with enhanced logic).
    * **Date of Transaction / Billing Period:** Captures the relevant date.
    * **Amount:** Extracts the total expenditure.
    * **Category:** Infers expense categories (e.g., Groceries, Electronics, Restaurant) using rule-based keyword matching.
* **Robust Data Validation:** Utilizes Pydantic models to ensure data integrity and schema compliance throughout the application.
* **Persistent Data Storage:** Stores all extracted and validated data in a lightweight SQLite relational database, ensuring data consistency (ACID properties) and optimized search performance through indexing.
* **Interactive Dashboard:** A user-friendly Streamlit interface to:
    * Display a tabular view of all uploaded and parsed receipts.
    * Apply dynamic **filters** (by vendor, category, date range, amount range).
    * Perform **in-memory sorting** on various fields (date, amount, vendor, category) in ascending or descending order.
* **Insightful Visualizations:** Provides clear financial overviews:
    * **Overall Expenditure Statistics:** Calculates and displays total, average, median, and mode of spending.
    * **Vendor Distribution:** Visualizes purchase frequency from different vendors using intuitive bar charts.
    * **Category Distribution:** Shows spending breakdown by inferred categories using engaging pie/donut charts.
    * **Monthly Spend Trend:** Tracks expenditure over time with clear line graphs.
* **Data Management Capabilities:**
    * **Manual Correction:** Allows users to easily edit any parsed fields directly via the UI for accuracy.
    * **Deletion:** Enables removal of individual receipt entries from the database.
* **Data Export:** Facilitates downloading of currently filtered data in both `.csv` and `.json` formats for external analysis.

## 🛠️ Technology Stack

This project leverages a modern full-stack Python ecosystem:

* **Backend Framework:** [FastAPI](https://fastapi.tiangolo.com/) - A high-performance, easy-to-use web framework for building APIs.
* **Database:** [SQLite](https://www.sqlite.org/index.html) - A lightweight, file-based relational database.
* **Database ORM:** [SQLModel](https://sqlmodel.tiangolo.com/) - A library for interacting with SQL databases, combining the power of SQLAlchemy and Pydantic.
* **Data Validation:** [Pydantic](https://pydantic.dev/) - Data validation and settings management using Python type hints.
* **OCR Engine:** [Tesseract-OCR](https://tesseract-ocr.github.io/) (via [pytesseract](https://pypi.org/project/pytesseract/)) - Optical Character Recognition for text extraction.
* **File Handling:** [Pillow](https://python-pillow.org/) (PIL) for image processing, [PyPDF2](https://pypi.org/project/PyPDF2/) for PDF text extraction.
* **Data Manipulation:** [Pandas](https://pandas.pydata.org/) & [NumPy](https://numpy.org/) - Essential libraries for data analysis and numerical operations.
* **Frontend/Dashboard:** [Streamlit](https://streamlit.io/) - An open-source app framework for rapidly building beautiful data apps.
* **Data Visualization:** [Plotly Express](https://plotly.com/python/plotly-express/) - High-level API for creating interactive plots.
* **HTTP Requests:** [Requests](https://requests.readthedocs.io/en/latest/) - Python HTTP library.
* **Version Control:** [Git](https://git-scm.com/) & [GitHub](https://github.com/) - For collaborative development and code hosting.

## 📂 Project Structure

The project is organized into a modular and clean directory structure:


bill-receipt-insight-extractor/
├── backend/                  # FastAPI backend application
│   ├── api/                  # Main FastAPI application and API endpoints
│   ├── core/                 # Core business logic: validation, parsing, algorithms
│   │   ├── algorithms.py     # Search, sort, and aggregation functions
│   │   ├── parser.py         # OCR and rule-based data extraction logic
│   │   └── validation.py     # Pydantic models for data schemas
│   ├── database/             # Database connection, ORM models, and CRUD operations
│   │   ├── crud.py           # Functions for interacting with the database
│   │   └── models.py         # SQLModel ORM definitions
│   └── init.py           # Marks 'backend' as a Python package
├── frontend/                 # Streamlit frontend application
│   └── app.py                # Streamlit dashboard code
├── data/                     # (Optional) Directory for temporary file storage or sample data
├── .gitignore                # Specifies intentionally untracked files to ignore
├── README.md                 # Project documentation (this file!)
└── requirements.txt          # List of Python dependencies


## ⚙️ Setup Instructions

Follow these steps to get the project up and running on your local machine.

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/bill-receipt-insight-extractor.git](https://github.com/your-username/bill-receipt-insight-extractor.git)
    cd bill-receipt-insight-extractor
    ```
    *(Replace `your-username` with your actual GitHub username)*

2.  **Set up Python Virtual Environment:**
    ```bash
    python -m venv venv
    ```

3.  **Activate the Virtual Environment:**
    * **On Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    * **On macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```

4.  **Create `requirements.txt` and Initial Project Files:**
    * Ensure your terminal is in the project root directory (`bill-receipt-insight-extractor`).
    * Create `requirements.txt`:
        ```bash
        # For macOS/Linux
        touch requirements.txt
        # For Windows
        type nul > requirements.txt
        ```
    * Create main subdirectories:
        ```bash
        mkdir backend frontend data
        ```
    * Create nested backend directories:
        ```bash
        mkdir backend\api  # Use backslash for Windows Command Prompt
        mkdir backend\core # Use backslash for Windows Command Prompt
        mkdir backend\database # Use backslash for Windows Command Prompt
        ```
    * Create empty Python files (use `type nul >` for Windows):
        ```bash
        type nul > backend\api\main.py
        type nul > backend\core\validation.py
        type nul > backend\core\parser.py
        type nul > backend\core\algorithms.py
        type nul > backend\database\models.py
        type nul > backend\database\crud.py
        type nul > frontend\app.py
        ```
    * Create `__init__.py` files to mark directories as Python packages (use `type nul >` for Windows):
        ```bash
        type nul > backend\__init__.py
        type nul > backend\api\__init__.py
        type nul > backend\core\__init__.py
        type nul > backend\database\__init__.py
        ```
    * Create `README.md` (this file):
        ```bash
        type nul > README.md
        ```
        *(You will paste this entire content into `README.md` after all other files are populated)*

5.  **Install Python dependencies:**
    * **Add the following content to your `requirements.txt` file (open `requirements.txt` in your editor and paste):**
        ```
        fastapi
        uvicorn[standard]
        sqlmodel
        pytesseract
        Pillow
        PyPDF2
        pandas
        numpy
        matplotlib
        plotly
        streamlit
        python-multipart
        requests
        ```
    * **Save `requirements.txt`.**
    * **Install them from your activated virtual environment:**
        ```bash
        pip install -r requirements.txt
        ```

6.  **Install Tesseract-OCR Engine (System-Level):**
    `pytesseract` is a Python wrapper; you need the actual Tesseract OCR engine installed on your system.

    * **On Windows (Recommended):**
        1.  Download the installer from [Tesseract at UB Mannheim](https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-v5.5.0.20241111.exe) (or a newer version if available).
        2.  Run the installer. During installation, make sure to:
            * Select "Install for all users."
            * **Check "Add tesseract to your PATH environment variable"** (very important!).
            * Optional: Select additional language data (e.g., Hindi, Kannada, Tamil) if you plan to process multi-language receipts.
        3.  After installation, **restart your terminal/command prompt** (and VS Code if open) for the updated PATH to take effect.
        4.  Verify installation by typing `tesseract --version` in your terminal.
    * **On macOS (using Homebrew):**
        ```bash
        brew install tesseract
        ```
    * **On Linux (Debian/Ubuntu):**
        ```bash
        sudo apt update
        sudo apt install tesseract-ocr
        sudo apt install libtesseract-dev # For development headers
        ```
    * **Important Note for `pytesseract`:** If `pytesseract` still cannot find Tesseract after installation, you might need to explicitly set the path in your `backend/core/parser.py` file. Uncomment and modify this line at the top of `backend/core/parser.py`:
        `pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'` (adjust to your actual path).

7.  **Populate Code Files:**
    * Copy and paste the code into the respective files as provided in previous steps (`backend/database/models.py`, `backend/database/crud.py`, `backend/core/validation.py`, `backend/core/parser.py`, `backend/core/algorithms.py`, `backend/api/main.py`, `frontend/app.py`).
    * **Ensure you save each file after pasting its content.**

## 🚀 How to Run

You will need two separate terminal windows (or tabs in VS Code) for the backend and frontend.

1.  **Start the Backend API (in Terminal 1):**
    * Open a new terminal and activate your virtual environment.
    * **Ensure you are in the project root directory** (`bill-receipt-insight-extractor`).
    * Run the FastAPI application:
        ```bash
        uvicorn backend.api.main:app --reload
        ```
    * The API will run on `http://127.0.0.1:8000`. You can view its interactive documentation at `http://127.0.0.1:8000/docs`.

2.  **Start the Frontend Dashboard (in Terminal 2):**
    * Open another new terminal and activate your virtual environment.
    * **Ensure you are in the project root directory** (`bill-receipt-insight-extractor`).
    * Run the Streamlit application:
        ```bash
        streamlit run frontend/app.py
        ```
    * The Streamlit dashboard will open in your web browser, typically at `http://localhost:8501`.

## 📋 Usage Guide

1.  **Upload Receipts:** Navigate to the "Upload & View Receipts" tab. Use the file uploader to select and upload your receipt/bill files (TXT, JPG, PNG, PDF). The application will parse the data and display it in a table.
2.  **Filter & Sort:** Use the search bars, date picker, and amount inputs to filter the displayed receipts. Experiment with the "Sort by" and "Direction" options to reorder the table.
3.  **View Insights:** Switch to the "Insights & Visualizations" tab to see aggregated statistics, vendor distribution, category breakdown, and monthly spending trends.
4.  **Administer Data:** Use the "Admin (Manual Correction)" tab to select a receipt, manually edit its parsed fields, or delete it from the database.
5.  **Export Data:** On the "Upload & View Receipts" tab, use the "Download as CSV" or "Download as JSON" buttons to export your currently filtered data.

## ⚠️ Limitations

* **Rule-Based Parsing Sensitivity:** The current data parsing relies heavily on regular expressions and keyword matching. This approach is effective for common receipt layouts but can be brittle and may not work perfectly for highly varied or unconventional receipt formats. OCR accuracy also depends on the quality of the uploaded image/PDF.
* **SQLite for Local Development:** While convenient for a mini-application and local development, SQLite is a file-based database. It is generally not suitable for multi-user, highly concurrent, or production deployments where data persistence across server restarts or seamless scalability is critical. Data may be lost if the database file is not properly managed during deployment.
* **No User Authentication:** The application is designed as a single-user tool and does not currently implement any user authentication or authorization features. All data is accessible to anyone running the application.
* **Basic Error Handling:** While core error handling is in place, a robust production application would require more comprehensive logging, detailed user feedback for all edge cases, and potentially a centralized error reporting system.
* **Streamlit UI Quirks:** Minor visual rendering glitches may occasionally occur with Streamlit's `st.dataframe` when custom CSS is heavily applied (e.g., jumbled text in column options). These are often related to Streamlit's internal rendering mechanisms and typically do not impact core functionality.

## 🌱 Future Enhancements (Stretch Goals)

This project can be significantly expanded with the following features:

* **User Authentication & Authorization:** Implement secure user registration and login functionality (e.g., using OAuth, JWT) to enable multi-user support and private data management.
* **Advanced AI/ML for Parsing:** Integrate more sophisticated machine learning models for data extraction, such as:
    * **Named Entity Recognition (NER):** Train custom NER models (e.g., with spaCy, Hugging Face Transformers) to robustly identify entities like vendor, date, and amount regardless of layout.
    * **Document Layout Analysis:** Use libraries like `layoutparser` to understand the visual structure of receipts and improve extraction accuracy.
* **Currency Detection & Conversion:** Automatically detect the currency of transactions and offer conversion to a user-defined base currency for unified financial analysis.
* **Machine Learning-based Categorization:** Develop and train a text classification model (e.g., using TF-IDF + SVM, or fine-tuning a small BERT model) to automatically assign categories more intelligently than simple keyword matching.
* **Predictive Analytics:** Implement time-series forecasting models (e.g., ARIMA, Prophet) to predict future spending trends based on historical data.
* **Cloud Deployment:** Deploy the entire full-stack application to a scalable cloud platform (e.g., Render, Google Cloud Run, AWS App Runner, Azure App Service) using a managed relational database service (e.g., PostgreSQL, MySQL) for robust data persistence and scalability.
* **Enhanced UI/UX:** Further refine the visual design, add more interactive elements, implement dark mode, and ensure full mobile responsiveness.
* **Notifications & Alerts:** Implement logic to detect unusual spending patterns or budget overruns and provide notifications to the user.
* **Image Preprocessing for OCR:** Integrate advanced image processing techniques (e.g., deskewing, binarization, noise reduction) before passing images to Tesseract for even higher OCR accuracy.

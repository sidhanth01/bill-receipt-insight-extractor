Bill & Receipt Insight Extractor
🚀 Project Objective
Develop a full-stack mini-application that allows users to seamlessly upload receipts and bills in various formats (.jpg, .png, .pdf, .txt). The application extracts structured data from these documents using rule-based logic and OCR, then presents summarized financial insights such as total spend, top vendors, and billing trends through an interactive user interface. The core focus is on applying fundamental algorithms (searching, sorting, aggregation) with clean backend logic and an intuitive UI.

✨ Features
Heterogeneous File Ingestion: Supports uploading .jpg, .png, .pdf, and .txt files.

Intelligent Data Parsing: Extracts key structured data fields including:

Vendor / Biller Name (with improved parsing logic)

Date of Transaction / Billing Period

Amount

Category (inferred from keywords like "Groceries", "Electronics", "Restaurant", etc.)

Robust Data Validation: Implements Pydantic models for formal type-checking and data integrity.

Persistent Data Storage: Stores extracted data in a lightweight SQLite relational database, ensuring ACID compliance and indexed for optimized search.

Dynamic Data Display: Presents uploaded and parsed receipts in a tabular view.

Interactive Filtering & Sorting:

Filtering: Allows users to filter receipts by vendor, category, date range, and amount range.

Sorting: Enables in-memory sorting of displayed data by transaction date, amount, vendor, and category (with secondary sorting for dates).

Financial Insights & Visualizations:

Overall Expenditure Statistics: Displays total, average, median, and mode of spending.

Vendor Distribution: Visualizes the frequency of purchases from different vendors using bar charts.

Category Distribution: Shows spending breakdown by category using pie/donut charts.

Monthly Spend Trend: Presents time-series expenditure graphs using line charts.

Manual Data Correction (Admin Panel): Provides an interface for users to manually edit any parsed fields for accuracy.

Data Deletion (Admin Panel): Allows users to delete individual receipt entries.

Data Export: Enables downloading of currently filtered data as .csv or .json files.

Modern UI/UX: Features a clean, intuitive interface with custom styling, consistent typography (Inter font), and responsive design.

🛠️ Technologies Used
Backend Framework: FastAPI (Python) - For building high-performance APIs.

Database: SQLite - Lightweight relational database.

Database ORM: SQLModel - Combines SQLAlchemy and Pydantic for elegant database interactions.

Data Validation: Pydantic - For defining and enforcing data schemas.

OCR (Optical Character Recognition): Tesseract-OCR (via pytesseract) - For extracting text from images and PDFs.

File Handling/Image Processing: Pillow, PyPDF2.

Data Manipulation: Pandas, NumPy.

Frontend/Dashboard: Streamlit - For rapid development of interactive web applications.

Data Visualization: Plotly Express (integrated with Streamlit).

HTTP Requests: Requests library.

Version Control: Git & GitHub.

⚙️ Setup Instructions
Follow these steps to get the project up and running on your local machine.

Clone the repository:

git clone https://github.com/your-username/bill-receipt-insight-extractor.git
cd bill-receipt-insight-extractor

(Replace your-username with your actual GitHub username)

Set up Python Virtual Environment:

python -m venv venv

Activate the Virtual Environment:

On Windows:

.\venv\Scripts\activate

On macOS/Linux:

source venv/bin/activate

Create requirements.txt and Initial Empty Files:

Ensure you are in the project root directory (bill-receipt-insight-extractor).

Create requirements.txt:

# For macOS/Linux
touch requirements.txt
# For Windows
type nul > requirements.txt

Create subdirectories:

mkdir backend frontend data
mkdir backend\api
mkdir backend\core
mkdir backend\database

Create empty Python files (use type nul > for Windows):

type nul > backend\api\main.py
type nul > backend\core\validation.py
type nul > backend\core\parser.py
type nul > backend\core\algorithms.py
type nul > backend\database\models.py
type nul > backend\database\crud.py
type nul > frontend\app.py

Create __init__.py files to mark directories as Python packages (use type nul > for Windows):

type nul > backend\__init__.py
type nul > backend\api\__init__.py
type nul > backend\core\__init__.py
type nul > backend\database\__init__.py

Create README.md:

type nul > README.md

(You will paste this entire content into README.md later)

Install Python dependencies:

Add the following content to your requirements.txt file (open requirements.txt in your editor and paste):

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

Save requirements.txt.

Install them from your activated virtual environment:

pip install -r requirements.txt

Install Tesseract-OCR Engine (System-Level):
pytesseract is a Python wrapper; you need the actual Tesseract OCR engine installed on your system.

On Windows (Recommended):

Download the installer from Tesseract at UB Mannheim (or a newer version if available).

Run the installer. During installation, make sure to:

Select "Install for all users."

Check "Add tesseract to your PATH environment variable" (very important!).

Select additional language data (e.g., Hindi, Kannada, Tamil) if you plan to process multi-language receipts.

After installation, restart your terminal/command prompt (and VS Code if open) for the PATH changes to take effect.

Verify installation by typing tesseract --version in your terminal.

On macOS (using Homebrew):

brew install tesseract

On Linux (Debian/Ubuntu):

sudo apt update
sudo apt install tesseract-ocr
sudo apt install libtesseract-dev # For development headers

Important Note for pytesseract: If pytesseract still cannot find Tesseract after installation, you might need to explicitly set the path in your backend/core/parser.py file. Uncomment and modify this line at the top of backend/core/parser.py:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' (adjust to your actual path).

Populate Code Files:

Copy and paste the code into the respective files as provided in the previous steps (backend/database/models.py, backend/database/crud.py, backend/core/validation.py, backend/core/parser.py, backend/core/algorithms.py, backend/api/main.py, frontend/app.py).

Ensure you save each file after pasting its content.

🚀 How to Run
You will need two separate terminal windows (or tabs in VS Code) for the backend and frontend.

Start the Backend API (in Terminal 1):

Open a new terminal and activate your virtual environment.

Ensure you are in the project root directory (bill-receipt-insight-extractor).

Run the FastAPI application:

uvicorn backend.api.main:app --reload

The API will run on http://127.0.0.1:8000. You can view its interactive documentation at http://127.0.0.1:8000/docs.

Start the Frontend Dashboard (in Terminal 2):

Open another new terminal and activate your virtual environment.

Ensure you are in the project root directory (bill-receipt-insight-extractor).

Run the Streamlit application:

streamlit run frontend/app.py

The Streamlit dashboard will open in your web browser, typically at http://localhost:8501.

⚠️ Limitations
Rule-Based Parsing: The data parsing relies on regular expressions and keyword matching, which can be brittle and may not work perfectly for all receipt formats. OCR accuracy can also vary with image quality.

SQLite for Persistence: While convenient for a mini-app, SQLite is a file-based database and is not ideal for multi-user, highly concurrent, or production deployments where data persistence across server restarts or scaling is critical.

No User Authentication: The current application is single-user and does not have login/signup functionality.

Basic Error Handling: While some error handling is in place, a production application would require more comprehensive logging and user feedback for all edge cases.

UI Rendering Quirks: Some minor visual glitches may occur with Streamlit's st.dataframe when custom CSS is heavily applied (e.g., jumbled text in column options), which are often related to Streamlit's internal rendering.

🌱 Future Enhancements (Stretch Goals)
User Authentication & Multi-User Support: Implement secure login/registration and allow users to manage their own private receipts.

Advanced OCR/NLP Integration: Explore machine learning models (e.g., custom Named Entity Recognition with spaCy/Transformers) for more robust and accurate data extraction from diverse receipt layouts.

Currency Detection & Conversion: Automatically detect currency symbols and offer conversion to a base currency for unified financial tracking.

Machine Learning-based Categorization: Train a text classification model to automatically categorize expenses more intelligently.

Predictive Analytics: Implement time-series forecasting to predict future spending trends.

Cloud Deployment: Deploy the FastAPI backend to a cloud platform (e.g., Render, Google Cloud Run, AWS App Runner) with a managed database (e.g., PostgreSQL) for scalability and persistence.

Enhanced UI/UX: Further refine the visual design, add more interactive elements, and improve mobile responsiveness.

Notifications/Alerts: Implement alerts for unusual spending patterns or budget overruns.

Image Preprocessing for OCR: Add image enhancement steps (e.g., deskewing, binarization) before passing to Tesseract for improved accuracy.
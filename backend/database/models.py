# backend/database/models.py

from typing import Optional
from sqlmodel import Field, SQLModel, create_engine
from datetime import date

# Define the database file name
# Relative path from backend/ to the project root
# Ensure this path is correct based on where your backend folder is relative to receipts.db
DATABASE_FILE = "../receipts.db"
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True) # echo=True logs SQL statements for debugging

class Receipt(SQLModel, table=True):
    """
    Represents a single receipt or bill entry in the database.
    SQLModel combines SQLAlchemy and Pydantic for easy ORM and data validation.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    vendor: str = Field(index=True) # Index for faster searches by vendor
    transaction_date: date = Field(index=True) # Index for faster searches by date
    amount: float = Field(index=True) # Index for faster searches by amount
    category: Optional[str] = Field(default=None, index=True) # Optional category, also indexed
    original_filename: str # Store the name of the original uploaded file

    # Optional: Add a method to represent the object nicely for debugging
    def __repr__(self):
        return f"Receipt(id={self.id}, vendor='{self.vendor}', date={self.transaction_date}, amount={self.amount}, category='{self.category}')"

def create_db_and_tables():
    """
    Creates the database tables based on the SQLModel definitions.
    This function should be called once when the application starts.
    """
    SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    # This block runs only when models.py is executed directly
    # Useful for initial database setup or testing the model creation
    print("Creating database and tables...")
    create_db_and_tables()
    print("Database and tables created successfully!")

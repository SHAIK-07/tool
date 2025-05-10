import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
if os.path.exists(".env"):
    load_dotenv()

# Set to False since we're not using cloud deployment
IN_GCP = False

# We'll use SQLite by default for local development
DATABASE_URL = None  # Will use SQLite as fallback
print("Using SQLite database")

# Other configuration settings
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-development-only")

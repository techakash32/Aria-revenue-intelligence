"""Root Streamlit entry point.

Run with:
    streamlit run app.py
"""
from dotenv import load_dotenv

load_dotenv()
from dashboard.app import main

if __name__ == "__main__":
    main()

"""Revenue Guardian project entry point."""
from dotenv import load_dotenv

load_dotenv()

def main() -> None:
    load_dotenv()
    print("ARIA Revenue Guardian")
    print("---------------------")
    print("Dashboard : streamlit run app.py")
    print("API Server: uvicorn api.main:app --reload")
    print("Seed DB   : python data/seed_db.py")


if __name__ == "__main__":
    main()

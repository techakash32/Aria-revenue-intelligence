from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

from api.routes import chat, health, trigger

app = FastAPI(
    title="Revenue Guardian API",
    version="0.1.0",
    description="API for the ARIA Revenue Guardian demo.",
)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(trigger.router)

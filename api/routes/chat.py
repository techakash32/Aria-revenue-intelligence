from fastapi import APIRouter
from pydantic import BaseModel

from pipelines.monitor_pipeline import run_monitor
from tools.llm_tool import answer_business_question

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


@router.post("")
async def chat(request: ChatRequest):
    message = request.message.strip()
    if should_run_monitor(message):
        result = await run_monitor(query=message)
        return {"reply": result.get("final_report"), "result": result}

    reply = await answer_business_question(message)
    return {"reply": reply, "received": request.message}


def should_run_monitor(message: str) -> bool:
    lowered = message.lower()
    keywords = ("revenue", "sales", "anomaly", "drop", "spike", "monitor")
    return any(keyword in lowered for keyword in keywords)

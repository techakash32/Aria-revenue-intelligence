from fastapi import APIRouter

from pipelines.monitor_pipeline import run_monitor

router = APIRouter(prefix="/trigger", tags=["trigger"])


@router.post("/daily-monitor")
async def daily_monitor():
    result = await run_monitor()
    return {"status": "completed", "result": result}

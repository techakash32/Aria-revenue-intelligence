from fastapi import APIRouter, Depends

from api.dependencies import Settings, get_settings

router = APIRouter(tags=["health"])


@router.get("/")
def root():
    return {"service": "revenue-guardian", "status": "ok"}


@router.get("/health")
def health_check(settings: Settings = Depends(get_settings)):
    return {
        "status": "ok",
        "integrations": {
            "groq_llm": bool(settings.groq_api_key),
            "whatsapp_alerts": settings.whatsapp_configured,
        },
        "config": {
            "anomaly_threshold_percent": settings.anomaly_threshold_percent,
            "max_iterations": settings.max_iterations,
        },
    }

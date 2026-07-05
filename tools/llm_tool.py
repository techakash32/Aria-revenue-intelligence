"""Groq-backed LLM helper with a deterministic fallback."""
from __future__ import annotations

import os

import httpx

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.1-8b-instant"


async def call_groq(system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return ""

    payload = {
        "model": os.getenv("GROQ_MODEL", DEFAULT_MODEL),
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()


async def interpret_anomaly(analytics: dict, anomaly: dict) -> str:
    fallback = anomaly.get("reason") or "No anomaly detected."
    try:
        response = await call_groq(
            system_prompt=(
                "You are ARIA, a concise revenue operations analyst. "
                "Explain revenue anomalies in plain business language. "
                "Do not invent causes. Keep the answer under 80 words."
            ),
            user_prompt=f"Analytics summary: {analytics}\nAnomaly result: {anomaly}",
        )
        return response or fallback
    except Exception:
        return fallback


async def answer_business_question(message: str, context: dict | None = None) -> str:
    context = context or {}
    if is_greeting(message):
        return (
            "Hi, I am ARIA. I can monitor revenue, detect drops or spikes, "
            "explain recent sales trends, and send Telegram alerts when something needs attention."
        )

    fallback = (
        "ARIA is running. Ask me to check revenue, find anomalies, explain sales trends, "
        "or run the monitor."
    )
    try:
        response = await call_groq(
            system_prompt=(
                "You are ARIA, a MySQL-backed revenue guardian assistant. "
                "Use only the provided context. If context is missing, say what data is needed."
            ),
            user_prompt=f"Question: {message}\nContext: {context}",
        )
        return response or fallback
    except Exception:
        return fallback


def is_greeting(message: str) -> bool:
    normalized = message.strip().lower()
    return normalized in {"hi", "hii", "hello", "hey", "yo", "namaste"}

import os
import re

import requests

WA_TOKEN    = os.getenv("WHATSAPP_TOKEN")
WA_PHONE_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WA_BASE     = f"https://graph.facebook.com/v19.0/{WA_PHONE_ID}" if WA_PHONE_ID else None

def sanitize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone.strip())
    if not digits:
        raise ValueError("Invalid phone number")
    if len(digits) == 10:
        return f"1{digits}"
    if len(digits) >= 7:
        return digits
    raise ValueError("Phone number too short")

def send_whatsapp_message(phone: str, message: str) -> bool:
    """Synchronous send – used internally."""
    if not WA_TOKEN or not WA_PHONE_ID:
        return False
    try:
        phone = sanitize_phone(phone)
    except ValueError:
        return False
    url = f"{WA_BASE}/messages"
    headers = {"Authorization": f"Bearer {WA_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": message}
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"[WhatsApp Error] {e}")
        return False

# ---------- The function your action_agent expects ----------
async def send_whatsapp_alert(message: str) -> dict:
    """
    Async wrapper to match the agent's call signature.
    Returns: {"sent": bool, "message_id": str | None, "reason": str | None}
    """
    recipient = os.getenv("WHATSAPP_RECIPIENT_ID")
    if not recipient:
        return {"sent": False, "reason": "No WHATSAPP_RECIPIENT_ID in env"}
    if not WA_TOKEN or not WA_PHONE_ID:
        return {"sent": False, "reason": "Missing WHATSAPP_TOKEN or WHATSAPP_PHONE_NUMBER_ID"}

    try:
        phone = sanitize_phone(recipient)
    except ValueError as e:
        return {"sent": False, "reason": f"Invalid phone: {e}"}

    url = f"{WA_BASE}/messages"
    headers = {"Authorization": f"Bearer {WA_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": message}
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        msg_id = data.get("messages", [{}])[0].get("id")
        return {"sent": True, "message_id": msg_id}
    except Exception as e:
        return {"sent": False, "reason": str(e)}

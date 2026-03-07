from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...db import get_db
from ...services.ai_tools import get_area_snapshot
from ...services.gemini_client import ask_gemini

router = APIRouter(prefix="/ai", tags=["ai"])


class ChatTurn(BaseModel):
    role: str   # "user" or "assistant"
    text: str


class ChatRequest(BaseModel):
    message: str
    lat: float
    lng: float
    radius_km: float = 1.5
    hour: int | None = None
    history: list[ChatTurn] = []
    
@router.get("/debug-env")
def debug_env():
    key = os.getenv("GEMINI_API_KEY")
    return {
        "has_key": bool(key),
        "key_prefix": key[:8] if key else None
    }   
@router.get("/test-gemini")
def test_gemini():
    try:
        reply = ask_gemini("Reply with exactly: Gemini is working.")
        return {"ok": True, "reply": reply}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@router.post("/chat")
def chat_ai(payload: ChatRequest, db: Session = Depends(get_db)):
    hour = payload.hour if payload.hour is not None else None

    snapshot = get_area_snapshot(
        db,
        lat=payload.lat,
        lng=payload.lng,
        radius_km=payload.radius_km,
        hour=hour,
    )

    history_text = "\n".join(
        [f'{turn.role.upper()}: {turn.text}' for turn in payload.history[-8:]]
    )

    prompt = f"""
You are Safescape AI, a calm, supportive, practical safety assistant.

Your job:
- Answer like a real conversational assistant, not like a template engine.
- Use the area context below.
- Be natural, warm, and specific.
- Do not invent any facts outside the provided context.
- If the user seems anxious, respond reassuringly first, then give practical next steps.
- Keep answers concise but human.

Area context:
- Average safety: {snapshot["avg_safety"]}
- Segments analyzed: {snapshot["segments_analyzed"]}
- Lower-safety segments: {snapshot["low_safety_segments"]}
- Anomaly segments: {snapshot["anomaly_segments"]}
- Safe points nearby: {snapshot["safe_points_nearby"]}
- Open 24/7 safe points: {snapshot["open_24x7_safe_points"]}
- Police points: {snapshot["police_points"]}
- Medical points: {snapshot["medical_points"]}
- Transit points: {snapshot["transit_points"]}
- Commercial points: {snapshot["commercial_points"]}
- Hour: {hour}

Recent conversation:
{history_text}

Latest user message:
{payload.message}

Write a helpful conversational reply.
"""

    try:
        reply = ask_gemini(prompt)
    except Exception:
        # backup only if Gemini fails
        avg = snapshot["avg_safety"]
        if avg >= 0.7:
            reply = "This area looks fairly safe right now. Stay on main roads and near active places."
        elif avg >= 0.45:
            reply = "This area looks moderately safe. I’d suggest staying on busier roads and near transit or commercial spots."
        else:
            reply = "This area looks relatively risky right now. Try moving toward a busier, well-lit place or a nearby safe point."

    return {
        "reply": reply,
        "snapshot": snapshot,
    }
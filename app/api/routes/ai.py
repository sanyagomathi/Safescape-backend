from fastapi import APIRouter
from pydantic import BaseModel
from ...services.gemini_client import ask_gemini

router = APIRouter(prefix="/ai", tags=["ai"])


class ChatRequest(BaseModel):
    message: str
    lat: float
    lng: float


@router.post("/chat")
def chat_ai(payload: ChatRequest):

    prompt = f"""
You are Safescape AI, an assistant that helps users understand safety in city areas.

User question:
{payload.message}

User location:
Latitude: {payload.lat}
Longitude: {payload.lng}

Give a short helpful answer about safety.
"""

    reply = ask_gemini(prompt)

    return {
        "reply": reply
    }
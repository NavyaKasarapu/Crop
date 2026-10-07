from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from backend.app.services.tts_service import tts_service

router = APIRouter(tags=["TTS / Speech"])


class TTSRequest(BaseModel):
    text: str
    language: str


@router.post("/api/tts")
@router.post("/api/speech")
def generate_speech(request: TTSRequest):
    text = request.text.strip()
    language = request.language.strip().lower()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Text is required."
        )

    if len(text) > 10000:
        raise HTTPException(
            status_code=400,
            detail="Text is too long."
        )

    if language not in {"en", "te", "hi"}:
        raise HTTPException(
            status_code=400,
            detail="Unsupported language. Supported: en, te, or hi."
        )

    try:
        audio = tts_service.synthesize(text, language)

        return Response(
            content=audio,
            media_type="audio/wav",
            headers={
                "Content-Disposition": "inline; filename=crop-disease-ai.wav"
            }
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Speech generation failed: {str(exc)}"
        )

import sys
from pathlib import Path

# Ensure both project root and backend folder are in sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
for directory in [str(PROJECT_ROOT), str(BACKEND_DIR)]:
    if directory not in sys.path:
        sys.path.insert(0, directory)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from backend.app.api.prediction import router as prediction_router
    from backend.app.api.tts import router as tts_router
    from backend.app.services.model_service import model_service
except ImportError:
    from app.api.prediction import router as prediction_router
    from app.api.tts import router as tts_router
    from app.services.model_service import model_service


app = FastAPI(
    title="Crop Disease AI API",
    description="AI-powered crop disease detection API using MobileNetV3 Small ONNX",
    version="1.0.0"
)

# Allow React/Vite frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(prediction_router)
app.include_router(tts_router)


@app.get("/")
def root():
    return {
        "message": "Crop Disease AI API is running",
        "status": "success",
        "model_loaded": model_service.is_available,
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "model_loaded": model_service.is_available,
        "model_available": model_service.is_available,
        "number_of_classes": len(model_service.class_names) if model_service.is_available else 0,
        "total_classes": len(model_service.class_names) if model_service.is_available else 0,
        "model_status": "loaded" if model_service.is_available else "unavailable",
        "unavailable_reason": model_service.unavailable_reason if not model_service.is_available else None
    }

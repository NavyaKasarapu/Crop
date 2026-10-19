import io
import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile, Query
from pydantic import BaseModel
from PIL import Image

from backend.app.services.model_service import model_service
from backend.app.services.severity_service import severity_service
from backend.app.services.weather_service import weather_service
from backend.app.services.translation_service import translation_service

router = APIRouter(prefix="/api", tags=["Crop Disease AI"])

ALLOWED_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# ---------------------------------------------------------
# Load disease knowledge base
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE_PATH = PROJECT_ROOT / "backend" / "app" / "data" / "disease_knowledge.json"

try:
    with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as file:
        DISEASE_KNOWLEDGE = json.load(file)
except Exception as error:
    print(f"[Prediction API] WARNING: Could not load disease knowledge base: {error}")
    DISEASE_KNOWLEDGE = {}


def normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    text = str(value).lower()
    for char in ["_", ",", "(", ")", "-"]:
        text = text.replace(char, " ")
    return " ".join(text.split())


def get_disease_information(crop: str, disease: str, predicted_class: Optional[str] = None):
    # 1. Direct exact class match in knowledge base
    if predicted_class and predicted_class in DISEASE_KNOWLEDGE:
        return DISEASE_KNOWLEDGE[predicted_class]

    target_crop = normalize_text(crop)
    target_disease = normalize_text(disease)

    # 2. Robust matching across all knowledge entries
    for class_name, info in DISEASE_KNOWLEDGE.items():
        if "___" in class_name:
            kc, kd = class_name.split("___", 1)
        else:
            kc, kd = class_name, ""
        
        nc = normalize_text(kc)
        nd = normalize_text(kd)

        # Check crop match (direct or word-level intersection)
        c_match = (nc == target_crop) or bool(set(nc.split()).intersection(set(target_crop.split())))
        # Check disease match
        d_match = (nd == target_disease) or (nd in target_disease) or (target_disease in nd)

        if c_match and d_match:
            return info

    return None


# ---------------------------------------------------------
# GET /api/model/classes
# ---------------------------------------------------------
@router.get("/model/classes")
def get_model_classes():
    if not model_service.is_available:
        raise HTTPException(
            status_code=503,
            detail=model_service.unavailable_reason or "AI model is currently unavailable. Please train/export the model first."
        )
    return {
        "success": True,
        "classes": model_service.class_names,
        "count": len(model_service.class_names),
    }


# ---------------------------------------------------------
# GET /api/supported-crops
# ---------------------------------------------------------
@router.get("/supported-crops")
def get_supported_crops():
    if not model_service.is_available or not model_service.class_names:
        raise HTTPException(
            status_code=503,
            detail=model_service.unavailable_reason or "AI model labels are currently unavailable."
        )
    crops = model_service.get_supported_crops()
    return {
        "success": True,
        "crops": crops,
        "count": len(crops),
        "total_classes": len(model_service.class_names),
    }


# ---------------------------------------------------------
# GET /api/weather
# ---------------------------------------------------------
@router.get("/weather")
def get_weather(
    latitude: float = Query(17.3850, description="Latitude"),
    longitude: float = Query(78.4867, description="Longitude")
):
    data = weather_service.get_weather(latitude=latitude, longitude=longitude)
    return data


# ---------------------------------------------------------
# Translation request models & POST /api/translate
# ---------------------------------------------------------
class TranslateRequest(BaseModel):
    text: Optional[str] = None
    texts: Optional[list] = None
    target_language: str = "en"


@router.post("/translate")
def translate(request: TranslateRequest):
    target_lang = request.target_language.strip().lower()
    if target_lang not in {"en", "te", "hi"}:
        raise HTTPException(status_code=400, detail="Unsupported language. Supported: en, te, hi.")

    if request.text is not None:
        translated = translation_service.translate(request.text, target_lang)
        return {"success": True, "target_language": target_lang, "translated_text": translated}

    if request.texts is not None:
        translated_list = translation_service.translate_list(request.texts, target_lang)
        return {"success": True, "target_language": target_lang, "translated_texts": translated_list}

    raise HTTPException(status_code=400, detail="Either 'text' or 'texts' must be provided.")


# ---------------------------------------------------------
# POST /api/predict
# ---------------------------------------------------------
@router.post("/predict")
async def predict(file: UploadFile = File(...)):
    # 1. MIME Validation
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported image format. Please upload JPG, JPEG, PNG, or WEBP."
        )

    # 2. File Read & Size Validation
    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    if len(image_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Image size ({len(image_bytes)/(1024*1024):.1f} MB) exceeds maximum allowed 10 MB limit."
        )

    # 3. Decode & Verify Image Integrity
    try:
        from PIL import ImageOps
        image = Image.open(io.BytesIO(image_bytes))
        image.verify()  # Check for corruption
        # Re-open after verify() according to PIL spec
        image = Image.open(io.BytesIO(image_bytes))
        image = ImageOps.exif_transpose(image)
        if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
            rgba = image.convert("RGBA")
            bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
            image = Image.alpha_composite(bg, rgba).convert("RGB")
        else:
            image = image.convert("RGB")
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is corrupted or could not be decoded as a valid image."
        )

    # 4. Model Availability Safety
    if not model_service.is_available:
        raise HTTPException(
            status_code=503,
            detail=model_service.unavailable_reason or "AI model is currently unavailable. Please train/export the model first."
        )

    # 5. Model Inference
    try:
        prediction_result = model_service.predict(image, filename=file.filename)
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(error)}"
        )

    predicted_crop = prediction_result.get("crop", "Unknown")
    predicted_disease = prediction_result.get("disease", "Unknown")
    condition = prediction_result.get("condition", "Unknown")
    is_unsupported = prediction_result.get("unsupported", False)
    status_category = prediction_result.get("status_category", "unsupported" if is_unsupported else "supported_diseased")
    status_label = prediction_result.get("status_label", "Supported crop — disease detected")
    predicted_class = prediction_result.get("predicted_class")

    is_uncertain = (status_category == "uncertain") or (condition == "Unable to identify confidently")
    is_unknown_img = (status_category == "unknown") or (condition == "Unknown")
    is_unsupported_crop = (status_category == "unsupported") or is_unsupported or (condition == "Unsupported")

    # 6. Severity & Affected Area Estimation (Only reliable for confident diagnoses)
    if is_unsupported_crop or is_unknown_img or is_uncertain:
        severity_result = {
            "severity": "N/A",
            "affected_area": "N/A",
            "health_score": None,
            "method": "N/A",
            "is_estimated": False,
            "details": "Severity analysis is only applicable to confident diagnoses on supported crop leaves."
        }
    else:
        try:
            severity_result = severity_service.estimate(image, predicted_crop, condition)
        except Exception as exc:
            print(f"[Prediction API] Severity estimation fallback: {exc}")
            severity_result = {
                "severity": "Unknown",
                "affected_area": "Unable to determine",
                "health_score": None,
                "method": "N/A",
                "is_estimated": False,
                "details": "Severity analysis unavailable."
            }

    # 7. Disease Knowledge & Recommendation Retrieval
    knowledge = None
    if not is_unsupported_crop and not is_unknown_img and not is_uncertain and condition != "Healthy":
        knowledge = get_disease_information(predicted_crop, predicted_disease, predicted_class)

    if knowledge:
        disease_info = {
            "available": True,
            "disease_name": knowledge.get("disease_name", predicted_disease),
            "crop_name": knowledge.get("crop_name", predicted_crop),
            "symptoms": knowledge.get("symptoms", []),
            "causes": knowledge.get("cause", ""),
            "recommendations": knowledge.get("recommendations", []),
            "prevention": knowledge.get("prevention", []),
        }
    elif condition == "Healthy":
        disease_info = {
            "available": True,
            "disease_name": "Healthy",
            "crop_name": predicted_crop,
            "symptoms": ["Normal healthy leaf coloration, vein structure, and cellular foliage observed."],
            "causes": "Plant foliage exhibits normal healthy cellular structure with no active pathogen colonization.",
            "recommendations": [
                "Maintain current irrigation, nutrient, and fertilizing regimen.",
                "Continue regular field scouting for early pest or disease pressure.",
            ],
            "prevention": [
                "Maintain good field sanitation, air circulation, and crop rotation.",
                "Ensure adequate drainage and avoid prolonged foliage dampness.",
            ],
        }
    elif is_uncertain:
        disease_info = {
            "available": False,
            "disease_name": "Unable to identify confidently",
            "crop_name": predicted_crop,
            "symptoms": ["Visual leaf symptoms are faint, ambiguous, or do not match a single pathogen profile with high certainty."],
            "causes": f"The leaf visual pattern matches {predicted_crop}, but specific foliar disease patterns lack definitive statistical confidence.",
            "recommendations": [
                f"The leaf appears to belong to {predicted_crop}, but the specific disease cannot be confirmed with sufficient confidence.",
                "Do not apply disease-specific chemical treatments or fungicides without on-site confirmation by an agronomist.",
                "Inspect multiple leaves across the crop canopy to check if clearer, characteristic lesions are present.",
            ],
            "prevention": [
                "Take a closer, high-resolution photograph of distinct lesion borders in natural daylight.",
                "Re-examine the plant in 48-72 hours if foliar symptoms progress.",
            ],
            "reason": "Supported crop identified, but disease is uncertain.",
        }
    elif is_unknown_img:
        disease_info = {
            "available": False,
            "disease_name": "N/A",
            "crop_name": "Unknown",
            "symptoms": ["Unable to resolve foliar details due to image blur, low light, or contrast issues."],
            "causes": "The image quality does not provide sufficient resolution or lighting for a definitive diagnosis.",
            "recommendations": [
                "Capture a sharper, close-up photograph of a single leaf in bright natural daylight.",
                "Ensure the camera lens is focused directly on the leaf surface and symptoms fill the frame.",
                "Hold the camera steady or place a hand behind the leaf if moving in the wind.",
            ],
            "prevention": [
                "Avoid blurry, underexposed, or overexposed captures.",
            ],
            "reason": "Image quality or clarity issue.",
        }
    elif is_unsupported_crop:
        disease_info = {
            "available": False,
            "disease_name": "N/A",
            "crop_name": predicted_crop,
            "symptoms": ["The visual pattern does not match any of the 14 supported crop species."],
            "causes": "The photograph is either not a crop leaf, or the plant species is outside the 14 supported crops.",
            "recommendations": [
                "This AI system is trained exclusively on 14 crops: Apple, Blueberry, Cherry, Corn, Grape, Orange, Peach, Bell Pepper, Potato, Raspberry, Soybean, Squash, Strawberry, and Tomato.",
                "Unsupported crops (e.g. rice, wheat, mango, banana, rose, weeds) cannot be reliably diagnosed by this model and must not be forced into a supported class.",
                "Consult your local agricultural extension service or a crop-specific pathology manual for unsupported crops.",
            ],
            "prevention": [
                "Check the Supported Crops list at the bottom of the Home page before uploading.",
            ],
            "reason": "Crop species or image is unsupported.",
        }
    else:
        disease_info = {
            "available": False,
            "disease_name": predicted_disease,
            "crop_name": predicted_crop,
            "symptoms": [],
            "causes": f"Disease pattern identified as {predicted_disease}.",
            "recommendations": [
                "Isolate symptomatic plants to prevent potential spread.",
                "Consult local agricultural extension service for specialized fungicide guidance.",
            ],
            "prevention": [
                "Sanitize pruning tools between cuts.",
                "Avoid overhead irrigation to minimize leaf moisture duration.",
            ],
            "reason": "General guidance applied.",
        }

    # 8. Complete unified response
    return {
        "success": True,
        "filename": file.filename,
        "result": {
            "status_category": status_category,
            "status_label": status_label,
            "crop": predicted_crop,
            "condition": condition,
            "disease": predicted_disease,
            "confidence": prediction_result.get("confidence", 0.0),
            "confidence_explanation": prediction_result.get(
                "confidence_explanation",
                model_service.CONFIDENCE_LIMITATION_EXPLANATION
            ),
            "quality_warning": prediction_result.get("quality_warning"),
            "probability_gap": prediction_result.get("probability_gap", 0.0),
            "reliability": prediction_result.get("reliability", "Low"),
            "reliability_message": prediction_result.get("reliability_message", ""),
            "health_status": prediction_result.get("health_status", "Unable to determine"),
            "unsupported": is_unsupported,
            "predicted_class": prediction_result.get("predicted_class"),
            "diagnostic_metrics": prediction_result.get("diagnostic_metrics", {}),
        },
        "severity": severity_result,
        "disease_info": disease_info,
        # Keep backwards compatibility for any component expecting symptoms at root
        "symptoms": {
            "available": disease_info["available"],
            "items": disease_info["symptoms"],
            "cause": disease_info["causes"],
            "recommendations": disease_info["recommendations"],
            "prevention": disease_info["prevention"],
        }
    }
import sys
import os
import json
import numpy as np
from pathlib import Path
from PIL import Image, ImageFilter
from collections import Counter

# Set unbuffered stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.model_service import model_service

# PlantDoc Test folder -> PlantVillage 38 class mapping
PLANTDOC_TO_PV = {
    "Apple leaf": "Apple___healthy",
    "Apple rust leaf": "Apple___Cedar_apple_rust",
    "Apple Scab Leaf": "Apple___Apple_scab",
    "Bell_pepper leaf": "Pepper,_bell___healthy",
    "Bell_pepper leaf spot": "Pepper,_bell___Bacterial_spot",
    "Blueberry leaf": "Blueberry___healthy",
    "Cherry leaf": "Cherry_(including_sour)___healthy",
    "Corn Gray leaf spot": "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn leaf blight": "Corn_(maize)___Northern_Leaf_Blight",
    "Corn rust leaf": "Corn_(maize)___Common_rust_",
    "Peach leaf": "Peach___healthy",
    "Potato leaf early blight": "Potato___Early_blight",
    "Potato leaf late blight": "Potato___Late_blight",
    "Raspberry leaf": "Raspberry___healthy",
    "Soyabean leaf": "Soybean___healthy",
    "Squash Powdery mildew leaf": "Squash___Powdery_mildew",
    "Strawberry leaf": "Strawberry___healthy",
    "Tomato Early blight leaf": "Tomato___Early_blight",
    "Tomato Septoria leaf spot": "Tomato___Septoria_leaf_spot",
    "Tomato leaf bacterial spot": "Tomato___Bacterial_spot",
    "Tomato leaf late blight": "Tomato___Late_blight",
    "Tomato leaf mosaic virus": "Tomato___Tomato_mosaic_virus",
    "Tomato leaf yellow virus": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato leaf": "Tomato___healthy",
    "Tomato mold leaf": "Tomato___Leaf_Mold",
    "grape leaf black rot": "Grape___Black_rot",
    "grape leaf": "Grape___healthy",
}

def evaluate_plantdoc_test():
    test_dir = PROJECT_ROOT / "data" / "plantdoc_extracted" / "test"
    if not test_dir.exists():
        print(f"[Eval] PlantDoc test directory not found at {test_dir}")
        return None

    results = []
    total = 0
    correct_crop = 0
    correct_disease = 0
    correct_exact = 0
    abstains = 0

    class_stats = {}

    for folder in sorted(test_dir.iterdir()):
        if not folder.is_dir():
            continue
        pv_target = PLANTDOC_TO_PV.get(folder.name)
        if not pv_target:
            continue

        target_crop, target_disease = pv_target.split("___")
        # normalize
        target_crop_clean = model_service._parse_class_name(pv_target)[0]

        files = list(folder.glob("*.*"))
        for img_path in files:
            try:
                with Image.open(img_path) as img:
                    img = img.convert("RGB")
                    pred = model_service.predict(img)

                total += 1
                is_unsupported = pred.get("unsupported", False)
                pred_class = pred.get("predicted_class")
                pred_crop = pred.get("crop")
                pred_condition = pred.get("condition")

                if is_unsupported or pred_condition in ("Unsupported", "Unknown"):
                    abstains += 1
                else:
                    if pred_crop == target_crop_clean:
                        correct_crop += 1
                    if pred_class == pv_target:
                        correct_exact += 1

                results.append({
                    "file": img_path.name,
                    "folder": folder.name,
                    "target_class": pv_target,
                    "target_crop": target_crop_clean,
                    "predicted_class": pred_class,
                    "predicted_crop": pred_crop,
                    "predicted_condition": pred_condition,
                    "confidence": pred.get("confidence", 0),
                    "unsupported": is_unsupported
                })
            except Exception as e:
                pass

    print("\n" + "=" * 65)
    print("REAL-WORLD FIELD EVALUATION (PlantDoc Test Set)")
    print("=" * 65)
    print(f"Total evaluated real-world images: {total}")
    print(f"Abstained as Unsupported / Unknown: {abstains} ({abstains/max(1, total)*100:.1f}%)")
    evaluated_total = total - abstains
    if evaluated_total > 0:
        print(f"Evaluated (Non-abstained): {evaluated_total}")
        print(f"Crop Accuracy (on evaluated): {correct_crop}/{evaluated_total} ({correct_crop/evaluated_total*100:.1f}%)")
        print(f"Exact Disease Accuracy (on evaluated): {correct_exact}/{evaluated_total} ({correct_exact/evaluated_total*100:.1f}%)")
    print(f"Overall Exact Top-1 Accuracy: {correct_exact}/{total} ({correct_exact/max(1, total)*100:.1f}%)")
    return {
        "total": total,
        "abstains": abstains,
        "correct_crop": correct_crop,
        "correct_exact": correct_exact,
        "overall_accuracy": round(correct_exact / max(1, total) * 100, 2)
    }

if __name__ == "__main__":
    evaluate_plantdoc_test()

import sys
import os
from pathlib import Path
import io

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root and backend to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

DATASET_ROOT = PROJECT_ROOT / "PlantVillage-Dataset" / "raw" / "color"

def run_tests():
    print("=" * 60)
    print("CROP DISEASE AI - END-TO-END VERIFICATION SUITE")
    print("=" * 60)

    # 1. Health & Model status
    print("\n[1] Testing GET /api/health ...")
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    health_data = res.json()
    print(f"    Status: {health_data['status']}, Model available: {health_data.get('model_available')}, Classes: {health_data.get('total_classes')}")
    assert health_data.get("model_available") is True

    # 2. Model classes
    print("\n[2] Testing GET /api/model/classes ...")
    res = client.get("/api/model/classes")
    assert res.status_code == 200
    classes_data = res.json()
    print(f"    Total supported dataset classes: {classes_data['count']}")
    assert classes_data["count"] == 38

    # 3. Weather
    print("\n[3] Testing GET /api/weather ...")
    res = client.get("/api/weather?latitude=17.3850&longitude=78.4867")
    assert res.status_code == 200
    w_data = res.json()
    print(f"    Weather available: {w_data.get('available')}, Temp: {w_data.get('temperature')}°C")

    # 4. Translation
    print("\n[4] Testing POST /api/translate ...")
    for lang, phrase in [("te", "Healthy"), ("hi", "Disease Detected"), ("te", "Unsupported Image / Crop")]:
        res = client.post("/api/translate", json={"text": phrase, "target_language": lang})
        assert res.status_code == 200
        print(f"    '{phrase}' -> ({lang}) : '{res.json().get('translated_text')}'")

    # 5. Speech synthesis for full text
    print("\n[5] Testing POST /api/speech (TTS narration) ...")
    narration_text = (
        "Crop pathology diagnostic report. Crop: Apple. Condition: Disease Detected. "
        "Identified condition: Black rot. Model confidence: 94 percent. "
        "Estimated severity level: Medium with approximately 14.5% affected leaf surface. "
        "Observed symptoms: Dark concentric rings on leaf blade. "
        "Underlying causes: Botryosphaeria obtusa fungal spores. "
        "Treatment recommendations: Apply protective fungicide and prune infected twigs. "
        "Preventive measures: Remove leaf litter and sanitize pruning shears."
    )
    res = client.post("/api/speech", json={"text": narration_text, "language": "en"})
    assert res.status_code == 200, f"Speech synthesis failed: {res.text}"
    assert len(res.content) > 10000, "Audio WAV is too small"
    print(f"    Full narration audio generated: {len(res.content):,} bytes WAV")

    # 6. Test Healthy images from multiple dataset crops
    print("\n[6] Testing Healthy Images from multiple crops ...")
    healthy_test_classes = [
        "Apple___healthy",
        "Grape___healthy",
        "Peach___healthy",
        "Soybean___healthy",
        "Tomato___healthy",
    ]
    for cls in healthy_test_classes:
        class_dir = DATASET_ROOT / cls
        if not class_dir.exists():
            print(f"    Skipping {cls} (dir not found)")
            continue
        imgs = list(class_dir.glob("*.*"))
        if not imgs:
            continue
        test_file = imgs[0]
        with open(test_file, "rb") as f:
            file_bytes = f.read()

        res = client.post(
            "/api/predict",
            files={"file": (test_file.name, file_bytes, "image/jpeg")}
        )
        assert res.status_code == 200, f"Prediction failed for {cls}: {res.text}"
        data = res.json()
        pred = data["result"]
        print(f"    {cls:25} -> Crop: {pred['crop']:12} Condition: {pred['condition']:16} Conf: {pred['confidence']:5.1f}% Status: {pred['health_status']}")
        assert pred["condition"] == "Healthy"
        assert pred["crop"] != "Unsupported Image / Crop"

    # 7. Test Diseased images from multiple dataset crops & classes
    print("\n[7] Testing Diseased Images from multiple crops ...")
    diseased_test_classes = [
        ("Apple___Apple_scab", "Apple"),
        ("Corn_(maize)___Common_rust_", "Corn"),
        ("Grape___Black_rot", "Grape"),
        ("Orange___Haunglongbing_(Citrus_greening)", "Orange"),
        ("Potato___Early_blight", "Potato"),
        ("Tomato___Late_blight", "Tomato"),
        ("Strawberry___Leaf_scorch", "Strawberry"),
    ]
    for cls, expected_crop in diseased_test_classes:
        class_dir = DATASET_ROOT / cls
        if not class_dir.exists():
            continue
        imgs = list(class_dir.glob("*.*"))
        if not imgs:
            continue
        test_file = imgs[0]
        with open(test_file, "rb") as f:
            file_bytes = f.read()

        res = client.post(
            "/api/predict",
            files={"file": (test_file.name, file_bytes, "image/jpeg")}
        )
        assert res.status_code == 200, f"Prediction failed for {cls}: {res.text}"
        data = res.json()
        pred = data["result"]
        disease_info = data.get("disease_info", {})
        print(f"    {cls:40} -> Crop: {pred['crop']:12} Disease: {pred['disease']:20} Conf: {pred['confidence']:5.1f}%")
        assert pred["condition"] == "Disease Detected"
        assert pred["crop"] == expected_crop
        assert pred["crop"] != "Unsupported Image / Crop"
        assert disease_info.get("available") is True
        assert len(disease_info.get("recommendations", [])) > 0

    # 8. Test Unsupported / Non-Crop image
    print("\n[8] Testing Unsupported / Non-crop Image ...")
    # Generate a pure non-crop pattern (solid white image or noise)
    from PIL import Image
    non_crop_img = Image.new("RGB", (224, 224), color=(128, 128, 128))
    buf = io.BytesIO()
    non_crop_img.save(buf, format="JPEG")
    non_crop_bytes = buf.getvalue()

    res = client.post(
        "/api/predict",
        files={"file": ("gray_neutral.jpg", non_crop_bytes, "image/jpeg")}
    )
    assert res.status_code == 200, f"Failed: {res.text}"
    data = res.json()
    pred = data["result"]
    print(f"    Non-crop image -> Crop: '{pred['crop']}' Condition: '{pred['condition']}' Unsupported: {pred['unsupported']}")
    assert pred["crop"] == "Unsupported Image / Crop"
    assert pred["condition"] == "Unsupported"
    assert pred["unsupported"] is True

    # Also test apple.jpg in workspace root if present
    if (PROJECT_ROOT / "apple.jpg").exists():
        with open(PROJECT_ROOT / "apple.jpg", "rb") as f:
            res = client.post("/api/predict", files={"file": ("apple.jpg", f.read(), "image/jpeg")})
            data = res.json()["result"]
            print(f"    Root apple.jpg -> Crop: '{data['crop']}' Condition: '{data['condition']}' Unsupported: {data['unsupported']}")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY! (100% End-to-End Verified)")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()

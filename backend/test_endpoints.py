import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def _find_sample_image() -> Path:
    """Locate a real leaf image from PlantVillage or PlantDoc dataset."""
    candidates = [
        PROJECT_ROOT / "PlantVillage-Dataset" / "raw" / "color" / "Apple___Apple_scab",
        PROJECT_ROOT / "data" / "plantdoc_extracted" / "test" / "Apple Scab Leaf",
        PROJECT_ROOT / "data" / "plantdoc_extracted" / "test" / "Apple leaf",
    ]
    for folder in candidates:
        if folder.is_dir():
            imgs = (
                list(folder.glob("*.jpg"))
                + list(folder.glob("*.JPG"))
                + list(folder.glob("*.png"))
            )
            if imgs:
                return imgs[0]
    raise FileNotFoundError(
        "No sample image found. Ensure PlantVillage-Dataset or "
        "data/plantdoc_extracted exists."
    )


def run_tests():
    print("\n--- 1. Testing GET /api/health ---")
    resp = client.get("/api/health")
    print("Status:", resp.status_code, "Body:", resp.json())
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
    assert resp.json()["model_loaded"] is True
    assert resp.json()["number_of_classes"] == 38

    print("\n--- 2. Testing GET /api/model/classes ---")
    resp = client.get("/api/model/classes")
    print("Status:", resp.status_code, "Count:", resp.json().get("count"))
    assert resp.status_code == 200
    assert resp.json()["count"] == 38

    print("\n--- 3. Testing GET /api/weather ---")
    resp = client.get("/api/weather?latitude=17.385&longitude=78.486")
    print("Status:", resp.status_code, "Weather condition:", resp.json().get("condition"))
    assert resp.status_code == 200

    print("\n--- 4. Testing POST /api/translate ---")
    resp = client.post("/api/translate", json={"text": "Healthy", "target_language": "te"})
    print("Telugu translation:", resp.json())
    assert resp.status_code == 200
    assert resp.json()["translated_text"] == "ఆరోగ్యంగా ఉంది"

    resp_hi = client.post(
        "/api/translate", json={"text": "Disease Detected", "target_language": "hi"}
    )
    print("Hindi translation:", resp_hi.json())
    assert resp_hi.status_code == 200
    assert resp_hi.json()["translated_text"] == "बीमारी पाई गई"

    print("\n--- 5. Testing POST /api/speech ---")
    resp = client.post("/api/speech", json={"text": "Apple scab detected", "language": "en"})
    print("Status:", resp.status_code, "Content length:", len(resp.content))
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "audio/wav"
    assert len(resp.content) > 1000

    print("\n--- 6. Testing POST /api/predict on valid leaf image ---")
    sample_img = _find_sample_image()
    print(f"Using image: {sample_img}")
    with open(sample_img, "rb") as f:
        resp = client.post(
            "/api/predict",
            files={"file": (sample_img.name, f, "image/jpeg")},
        )
    print("Status:", resp.status_code)
    data = resp.json()
    print("Success:", data["success"])
    result = data["result"]
    print("Crop:", result["crop"])
    print("Condition:", result["condition"])
    print("Disease:", result["disease"])
    print("Confidence:", result.get("confidence"), "%")
    print("Status Category:", result.get("status_category"))
    print("Status Label:", result.get("status_label"))
    diag = result.get("diagnostic_metrics")
    if diag:
        print(
            "Diagnostic metrics:",
            {k: round(v, 3) if isinstance(v, float) else v for k, v in diag.items()},
        )
    assert resp.status_code == 200
    assert data["success"] is True
    assert "severity" in data
    assert "disease_info" in data
    # New structured-response field assertions
    assert "status_category" in result, "Missing status_category"
    assert result["status_category"] in (
        "supported_healthy",
        "supported_diseased",
        "unsupported",
        "unknown",
    ), f"Unexpected status_category: {result['status_category']}"
    assert "status_label" in result, "Missing status_label"
    assert "diagnostic_metrics" in result, "Missing diagnostic_metrics"
    assert "confidence_explanation" in result, "Missing confidence_explanation"

    print("\n--- 7. Testing POST /api/predict with invalid file (text file) ---")
    resp = client.post(
        "/api/predict", files={"file": ("fake.txt", b"not an image", "text/plain")}
    )
    print("Status:", resp.status_code, "Detail:", resp.json().get("detail"))
    assert resp.status_code == 400

    print("\n--- 8. Testing POST /api/predict with corrupted image bytes ---")
    resp = client.post(
        "/api/predict", files={"file": ("corrupt.jpg", b"corrupted bytes", "image/jpeg")}
    )
    print("Status:", resp.status_code, "Detail:", resp.json().get("detail"))
    assert resp.status_code == 400

    print("\n--- 9. Testing POST /api/predict with oversized file (>10MB) ---")
    large_bytes = b"0" * (10 * 1024 * 1024 + 1024)
    resp = client.post(
        "/api/predict", files={"file": ("huge.jpg", large_bytes, "image/jpeg")}
    )
    print("Status:", resp.status_code, "Detail:", resp.json().get("detail"))
    assert resp.status_code == 400

    print("\n[ALL TESTS PASSED SUCCESSFULLY!]")


if __name__ == "__main__":
    run_tests()

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

    resp_hi = client.post("/api/translate", json={"text": "Disease Detected", "target_language": "hi"})
    print("Hindi translation:", resp_hi.json())
    assert resp_hi.status_code == 200
    assert resp_hi.json()["translated_text"] == "बीमारी पाई गई"

    print("\n--- 5. Testing POST /api/speech ---")
    resp = client.post("/api/speech", json={"text": "Apple scab detected", "language": "en"})
    print("Status:", resp.status_code, "Content length:", len(resp.content))
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "audio/wav"
    assert len(resp.content) > 1000

    print("\n--- 6. Testing POST /api/predict on valid image (apple.jpg) ---")
    sample_img = PROJECT_ROOT / "apple.jpg"
    with open(sample_img, "rb") as f:
        resp = client.post("/api/predict", files={"file": ("apple.jpg", f, "image/jpeg")})
    print("Status:", resp.status_code)
    data = resp.json()
    print("Crop:", data["result"]["crop"])
    print("Condition:", data["result"]["condition"])
    print("Disease:", data["result"]["disease"])
    print("Confidence:", data["result"]["confidence"], "%")
    print("Severity:", data["severity"]["severity"])
    print("Affected Area:", data["severity"]["affected_area"])
    print("Health Score:", data["severity"]["health_score"])
    print("Method:", data["severity"]["method"])
    print("Disease Info Symptoms:", len(data["disease_info"]["symptoms"]))
    print("Recommendations:", len(data["disease_info"]["recommendations"]))
    assert resp.status_code == 200
    assert data["success"] is True
    assert "severity" in data
    assert "disease_info" in data

    print("\n--- 7. Testing POST /api/predict with invalid file (text file) ---")
    resp = client.post("/api/predict", files={"file": ("fake.txt", b"not an image", "text/plain")})
    print("Status:", resp.status_code, "Detail:", resp.json().get("detail"))
    assert resp.status_code == 400

    print("\n--- 8. Testing POST /api/predict with corrupted image bytes ---")
    resp = client.post("/api/predict", files={"file": ("corrupt.jpg", b"corrupted bytes", "image/jpeg")})
    print("Status:", resp.status_code, "Detail:", resp.json().get("detail"))
    assert resp.status_code == 400

    print("\n--- 9. Testing POST /api/predict with oversized file (>10MB) ---")
    large_bytes = b"0" * (10 * 1024 * 1024 + 1024)
    resp = client.post("/api/predict", files={"file": ("huge.jpg", large_bytes, "image/jpeg")})
    print("Status:", resp.status_code, "Detail:", resp.json().get("detail"))
    assert resp.status_code == 400

    print("\n[ALL TESTS PASSED SUCCESSFULLY!]")


if __name__ == "__main__":
    run_tests()

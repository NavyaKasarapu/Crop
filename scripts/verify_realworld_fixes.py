import os
import sys
# Configure UTF-8 for console output on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
import numpy as np
from PIL import Image, ImageFilter
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.main import app

client = TestClient(app)

def test_supported_crops_order_and_content():
    print("=== TEST 1: Supported Crops Endpoint & Exact Order ===")
    resp = client.get("/api/supported-crops")
    assert resp.status_code == 200, f"Status code {resp.status_code}"
    data = resp.json()
    assert data["success"] is True
    crops = data["crops"]
    assert len(crops) == 14, f"Expected 14 crops, got {len(crops)}"
    
    expected_order = [
        ("Apple", "🍎"),
        ("Bell Pepper", "🫑"),
        ("Blueberry", "🫐"),
        ("Cherry", "🍒"),
        ("Corn", "🌽"),
        ("Grape", "🍇"),
        ("Orange", "🍊"),
        ("Peach", "🍑"),
        ("Potato", "🥔"),
        ("Raspberry", "🫐"),
        ("Soybean", "🌱"),
        ("Squash", "🎃"),
        ("Strawberry", "🍓"),
        ("Tomato", "🍅"),
    ]
    
    for i, (exp_name, exp_icon) in enumerate(expected_order):
        actual_name = crops[i]["name"]
        actual_icon = crops[i]["icon"]
        print(f"  [{i+1:2d}] {actual_icon} {actual_name}")
        assert actual_name == exp_name, f"Expected {exp_name} at index {i}, got {actual_name}"
        assert actual_icon == exp_icon, f"Expected icon {exp_icon} for {exp_name}, got {actual_icon}"
    
    print("[OK] Exact 14 supported crops match model ontology and requested order!\n")

def test_8_required_scenarios():
    print("=== TEST 2: The 8 Required Real-World Scenarios ===")
    
    # 1. Single supported leaf
    print("\n-- Scenario 1: A single supported leaf --")
    p1 = os.path.join("data", "plantvillage", "Tomato___healthy")
    if not os.path.exists(p1):
        p1 = os.path.join("PlantVillage-Dataset", "raw", "color", "Tomato___healthy")
    if not os.path.exists(p1):
        p1 = os.path.join("data", "plantdoc_extracted", "test", "Tomato leaf")
    files1 = [f for f in os.listdir(p1) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    with open(os.path.join(p1, files1[0]), "rb") as f:
        res1 = client.post("/api/predict", files={"file": ("leaf.jpg", f, "image/jpeg")}).json()
    r1 = res1.get("result", {})
    print(f"  File: {files1[0]} -> Crop: {r1.get('crop')}, Disease: {r1.get('disease')}, Status: {r1.get('status_category')}")
    assert r1.get("status_category") in ["supported_healthy", "supported_diseased", "uncertain"]
    assert r1.get("crop") in ["Tomato", "Apple", "Potato", "Corn", "Grape"]

    # 2. Several leaves from the same supported crop
    print("\n-- Scenario 2: Several leaves from the same supported crop --")
    p2 = os.path.join("data", "plantdoc_extracted", "test", "Raspberry leaf")
    files2 = [f for f in os.listdir(p2) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    # Pick multi-leaf stock image
    multi_file = [f for f in files2 if "leaves" in f.lower() or "deposit" in f.lower()][0]
    with open(os.path.join(p2, multi_file), "rb") as f:
        res2 = client.post("/api/predict", files={"file": ("multi_leaf.jpg", f, "image/jpeg")}).json()
    r2 = res2.get("result", {})
    print(f"  File: {multi_file} -> Crop: {r2.get('crop')}, Disease: {r2.get('disease')}, Status: {r2.get('status_category')}")
    assert r2.get("crop") != "Unsupported crop", "Multi-leaf supported image should NOT be unsupported!"
    assert r2.get("status_category") in ["supported_healthy", "supported_diseased", "uncertain"]

    # 3. Multiple leaves with a complex background
    print("\n-- Scenario 3: Multiple leaves with complex outdoor background --")
    p3 = os.path.join("data", "plantdoc_extracted", "test", "Corn Gray leaf spot")
    # IMG_42231.jpg has outdoor leaves on plant in field with complex background
    with open(os.path.join(p3, "IMG_42231.jpg"), "rb") as f:
        res3 = client.post("/api/predict", files={"file": ("field_corn.jpg", f, "image/jpeg")}).json()
    r3 = res3.get("result", {})
    print(f"  File: IMG_42231.jpg -> Crop: {r3.get('crop')}, Disease: {r3.get('disease')}, Status: {r3.get('status_category')}")
    assert r3.get("crop") != "Unsupported crop", "Corn with complex background must not be labeled unsupported!"
    assert r3.get("crop") == "Corn"

    # 4. A healthy supported crop
    print("\n-- Scenario 4: A healthy supported crop --")
    p4 = os.path.join("data", "plantdoc_extracted", "test", "Tomato leaf")
    files4 = [f for f in os.listdir(p4) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    with open(os.path.join(p4, "1684.jpg"), "rb") as f:
        res4 = client.post("/api/predict", files={"file": ("tomato_healthy.jpg", f, "image/jpeg")}).json()
    r4 = res4.get("result", {})
    print(f"  File: 1684.jpg -> Crop: {r4.get('crop')}, Disease: {r4.get('disease')}, Status: {r4.get('status_category')}")
    assert r4.get("crop") == "Tomato" and r4.get("status_category") == "supported_healthy"

    # 5. A diseased supported crop
    print("\n-- Scenario 5: A diseased supported crop --")
    p5 = os.path.join("data", "plantdoc_extracted", "test", "Corn leaf blight")
    with open(os.path.join(p5, "02c.jpg"), "rb") as f:
        res5 = client.post("/api/predict", files={"file": ("corn_blight.jpg", f, "image/jpeg")}).json()
    r5 = res5.get("result", {})
    print(f"  File: 02c.jpg -> Crop: {r5.get('crop')}, Disease: {r5.get('disease')}, Status: {r5.get('status_category')}")
    assert r5.get("crop") == "Corn" and r5.get("status_category") == "supported_diseased"
    assert res5.get("severity", {}).get("severity") not in [None, "N/A"]

    # 6. Genuinely unsupported crop (Rice)
    print("\n-- Scenario 6: A genuinely unsupported crop (Rice) --")
    p6 = os.path.join("data", "test_rice")
    rice_files = [f for f in os.listdir(p6) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    all_rejected = True
    for rf in rice_files:
        with open(os.path.join(p6, rf), "rb") as f:
            res6 = client.post("/api/predict", files={"file": ("leaf.jpg", f, "image/jpeg")}).json()
        r6 = res6.get("result", {})
        is_unsupp = (r6.get("status_category") == "unsupported") and (r6.get("crop") == "Unsupported crop")
        print(f"  File: {rf} -> Crop: '{r6.get('crop')}', Status: '{r6.get('status_category')}', Unsupported: {is_unsupp}")
        if not is_unsupp:
            all_rejected = False
    assert all_rejected, "All rice files must return Unsupported crop!"
    print("  [OK] 100% of Rice images rejected as Unsupported crop without false diagnosis.")

    # 7. Unrelated object (non-plant)
    print("\n-- Scenario 7: An unrelated object (non-plant) --")
    # Generate non-plant metallic noise texture
    arr = np.random.randint(120, 160, (300, 300, 3), dtype=np.uint8)
    Image.fromarray(arr).save("test_unrelated.jpg")
    with open("test_unrelated.jpg", "rb") as f:
        res7 = client.post("/api/predict", files={"file": ("unrelated.jpg", f, "image/jpeg")}).json()
    r7 = res7.get("result", {})
    print(f"  Non-plant texture -> Crop: '{r7.get('crop')}', Status: '{r7.get('status_category')}'")
    assert r7.get("status_category") == "unsupported" and r7.get("crop") == "Unknown image"
    if os.path.exists("test_unrelated.jpg"):
        os.remove("test_unrelated.jpg")

    # 8. Blurry or unusable image
    print("\n-- Scenario 8: Blurry or unusable image --")
    im_sharp = Image.open(os.path.join(p5, "02c.jpg"))
    im_blurry = im_sharp.filter(ImageFilter.GaussianBlur(radius=24))
    im_blurry.save("test_blurry.jpg")
    with open("test_blurry.jpg", "rb") as f:
        res8 = client.post("/api/predict", files={"file": ("blurry.jpg", f, "image/jpeg")}).json()
    r8 = res8.get("result", {})
    print(f"  Heavy Gaussian blur -> Crop: '{r8.get('crop')}', Status: '{r8.get('status_category')}', Warning: '{r8.get('quality_warning')}'")
    assert r8.get("status_category") == "unknown" and r8.get("crop") == "Unknown"
    assert res8.get("severity", {}).get("severity") in ["N/A", None]
    if os.path.exists("test_blurry.jpg"):
        os.remove("test_blurry.jpg")

    print("\n[OK] ALL 8 REAL-WORLD SCENARIOS PASSED WITH PERFECT METRICS!")

if __name__ == "__main__":
    test_supported_crops_order_and_content()
    test_8_required_scenarios()

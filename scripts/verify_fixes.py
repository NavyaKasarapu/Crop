import sys
from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.model_service import model_service

def run_all_tests():
    print("=" * 65)
    print("COMPREHENSIVE VERIFICATION & TEST SUITE")
    print("=" * 65)

    # 1. RICE TEST
    print("\n--- 1. Testing Rice Images (Must NOT be labeled Corn / Northern Leaf Blight) ---")
    rice_dir = PROJECT_ROOT / "data" / "test_rice"
    rice_files = [p for p in sorted(rice_dir.glob("*.jp*")) if "horses" not in p.name]
    assert len(rice_files) > 0, "No rice images found for testing!"
    for p in rice_files:
        with Image.open(p) as img:
            res = model_service.predict(img, filename=p.name)
            stat = res["status_category"]
            crop = res["crop"]
            dis = res["disease"]
            print(f"  {p.name:32} -> {stat:15} | crop: {crop:20} | disease: {dis}")
            assert "Corn" not in crop, f"FAILED: Rice was labeled as Corn in {p.name}"
            assert stat in ("unsupported", "unknown"), f"FAILED: Rice was not rejected in {p.name}"

    # 2. STRAWBERRY TEST
    print("\n--- 2. Testing Strawberry Images ---")
    pv_straw = PROJECT_ROOT / "PlantVillage-Dataset" / "raw" / "color" / "Strawberry___Leaf_scorch"
    pv_straw_files = list(pv_straw.glob("*.JPG"))[:5]
    for p in pv_straw_files:
        with Image.open(p) as img:
            res = model_service.predict(img, filename=p.name)
            stat = res["status_category"]
            crop = res["crop"]
            dis = res["disease"]
            conf = res["confidence"]
            print(f"  PV Scorch: {p.name[:25]:25} -> {stat:18} | crop: {crop:12} | {dis} ({conf}%)")
            assert crop == "Strawberry", f"FAILED: Crop was {crop}"
            assert stat in ("supported_diseased", "supported_healthy", "unknown")

    doc_straw = PROJECT_ROOT / "data" / "plantdoc_extracted" / "test" / "Strawberry leaf"
    if doc_straw.exists():
        for p in list(doc_straw.glob("*"))[:6]:
            with Image.open(p) as img:
                res = model_service.predict(img, filename=p.name)
                stat = res["status_category"]
                crop = res["crop"]
                dis = res["disease"]
                conf = res["confidence"]
                print(f"  Doc Straw: {p.name[:25]:25} -> {stat:18} | crop: {crop:12} | {dis} ({conf}%)")
                assert stat != "unsupported", f"FAILED: Real strawberry marked unsupported in {p.name}"

    # 3. CORN TEST
    print("\n--- 3. Testing Genuine Corn Images ---")
    corn_dir = PROJECT_ROOT / "PlantVillage-Dataset" / "raw" / "color" / "Corn_(maize)___Northern_Leaf_Blight"
    for p in list(corn_dir.glob("*.JPG"))[:4]:
        with Image.open(p) as img:
            res = model_service.predict(img, filename=p.name)
            stat = res["status_category"]
            crop = res["crop"]
            dis = res["disease"]
            conf = res["confidence"]
            print(f"  Corn NLB:  {p.name[:25]:25} -> {stat:18} | crop: {crop:12} | {dis} ({conf}%)")
            assert crop == "Corn"
            assert stat == "supported_diseased"

    # 4. HEALTHY LEAVES TEST
    print("\n--- 4. Testing Healthy Leaves ---")
    healthy_dir = PROJECT_ROOT / "PlantVillage-Dataset" / "raw" / "color" / "Apple___healthy"
    for p in list(healthy_dir.glob("*.JPG"))[:3]:
        with Image.open(p) as img:
            res = model_service.predict(img, filename=p.name)
            stat = res["status_category"]
            crop = res["crop"]
            dis = res["disease"]
            print(f"  Apple H:   {p.name[:25]:25} -> {stat:18} | crop: {crop:12} | {dis}")
            assert crop == "Apple"
            assert stat == "supported_healthy"

    # 5. UNRELATED OBJECTS TEST
    print("\n--- 5. Testing Unrelated Non-Leaf Objects ---")
    sky = Image.new("RGB", (300, 300), color=(100, 149, 237))
    res_sky = model_service.predict(sky, filename="sky.jpg")
    print(f"  Pure Blue: -> {res_sky['status_category']:18} | crop: {res_sky['crop']}")
    assert res_sky["status_category"] == "unsupported"

    np.random.seed(42)
    noise_img = Image.fromarray(np.random.randint(0, 256, (300, 300, 3), dtype=np.uint8))
    res_noise = model_service.predict(noise_img, filename="noise.jpg")
    print(f"  Noise:     -> {res_noise['status_category']:18} | crop: {res_noise['crop']}")
    assert res_noise["status_category"] == "unsupported"

    # 6. BLURRY IMAGES TEST
    print("\n--- 6. Testing Blurry Images ---")
    sharp_leaf = next(pv_straw.glob("*.JPG"))
    with Image.open(sharp_leaf) as orig:
        severe_blur = orig.filter(ImageFilter.GaussianBlur(radius=10))
        res_blur = model_service.predict(severe_blur, filename="blur.jpg")
        print(f"  Blur Leaf: -> {res_blur['status_category']:18} | label: '{res_blur['status_label']}'")
        assert res_blur["status_category"] == "unknown"
        assert "unable to identify crop or disease reliably" in res_blur["status_label"].lower()

    print("\n" + "=" * 65)
    print("ALL 6 TEST CATEGORIES PASSED WITH 100% ACCURACY!")
    print("=" * 65)

if __name__ == "__main__":
    run_all_tests()

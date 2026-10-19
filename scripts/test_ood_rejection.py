import sys
import io
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.model_service import model_service

def test_unrelated_and_ood():
    print("=" * 65)
    print("OOD & INPUT QUALITY REJECTION TEST (CURRENT MODEL)")
    print("=" * 65)

    test_cases = []

    # 1. Unrelated non-leaf images
    # Blue sky / wall
    sky = Image.new("RGB", (300, 300), color=(100, 149, 237))
    test_cases.append(("Pure Blue Image", sky, "Non-leaf / Unrelated"))

    # Random noise
    np.random.seed(42)
    noise_arr = np.random.randint(0, 256, (300, 300, 3), dtype=np.uint8)
    noise_img = Image.fromarray(noise_arr)
    test_cases.append(("Random Noise", noise_img, "Non-leaf / Unrelated"))

    # Indoor texture (wood/brown gradient)
    grad = Image.new("RGB", (300, 300))
    draw = ImageDraw.Draw(grad)
    for y in range(300):
        c = int(80 + (y / 300.0) * 80)
        draw.line([(0, y), (300, y)], fill=(c, c // 2, 20))
    test_cases.append(("Brown Wood Texture", grad, "Non-leaf / Unrelated"))

    # Red car / object color
    red_obj = Image.new("RGB", (300, 300), color=(220, 20, 30))
    draw = ImageDraw.Draw(red_obj)
    draw.rectangle([50, 50, 250, 250], fill=(30, 30, 30))
    test_cases.append(("Red/Dark Geometric Object", red_obj, "Non-leaf / Unrelated"))

    # 2. Severely blurry leaf images
    pv_dir = PROJECT_ROOT / "PlantVillage-Dataset" / "raw" / "color" / "Apple___Apple_scab"
    if pv_dir.exists():
        sample_leaf_path = next(pv_dir.glob("*.JPG"), None)
        if sample_leaf_path:
            with Image.open(sample_leaf_path) as orig_leaf:
                orig_leaf = orig_leaf.convert("RGB")
                test_cases.append(("Apple Leaf (Original Sharp)", orig_leaf.copy(), "Supported Diseased"))

                # Mild blur
                mild_blur = orig_leaf.filter(ImageFilter.GaussianBlur(radius=3))
                test_cases.append(("Apple Leaf (Mild Blur)", mild_blur, "Degraded Image"))

                # Severe blur
                severe_blur = orig_leaf.filter(ImageFilter.GaussianBlur(radius=10))
                test_cases.append(("Apple Leaf (Severe Blur)", severe_blur, "Blurry Image"))

                # Overexposed
                bright_arr = np.clip(np.array(orig_leaf, dtype=np.int32) + 120, 0, 255).astype(np.uint8)
                overexposed = Image.fromarray(bright_arr)
                test_cases.append(("Apple Leaf (Overexposed)", overexposed, "Poor Exposure"))

                # Underexposed (dark)
                dark_arr = np.clip(np.array(orig_leaf, dtype=np.float32) * 0.1, 0, 255).astype(np.uint8)
                underexposed = Image.fromarray(dark_arr)
                test_cases.append(("Apple Leaf (Underexposed)", underexposed, "Poor Exposure"))

    print(f"\nRunning {len(test_cases)} OOD/Degradation Test Cases:\n")
    for name, img, expected_category in test_cases:
        res = model_service.predict(img)
        print(f"[{name}] (Expected: {expected_category})")
        print(f"  -> Crop: '{res.get('crop')}', Disease: '{res.get('disease')}', Condition: '{res.get('condition')}'")
        print(f"  -> Conf: {res.get('confidence')}%, Gap: {res.get('probability_gap')}%, Unsupported: {res.get('unsupported')}")
        print(f"  -> Reliability: {res.get('reliability')} ({res.get('reliability_message')[:60]}...)")
        print()

if __name__ == "__main__":
    test_unrelated_and_ood()

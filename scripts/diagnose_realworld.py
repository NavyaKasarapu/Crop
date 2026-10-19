import os
import sys
sys.path.insert(0, os.path.abspath("."))
from PIL import Image
from backend.app.services.model_service import model_service

test_dir = "data/plantdoc_extracted/test"
print(f"Scanning categories in {test_dir}...")
count = 0
for category in sorted(os.listdir(test_dir)):
    cat_dir = os.path.join(test_dir, category)
    if os.path.isdir(cat_dir):
        files = [f for f in os.listdir(cat_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        for f in files[:2]:
            path = os.path.join(cat_dir, f)
            try:
                img = Image.open(path)
                res = model_service.predict(img)
                stat = res.get("status_category")
                crop = res.get("crop")
                dis = res.get("disease")
                conf = res.get("confidence")
                metrics = res.get("diagnostic_metrics", {})
                e = metrics.get("energy_score")
                zm = metrics.get("max_logit")
                print(f"[{category}] {f} -> status: {stat:12s} | crop: {crop:15s} | disease: {dis:25s} | conf: {conf}% | E: {e} | z_max: {zm}")
                count += 1
            except Exception as ex:
                print(f"[{category}] {f} -> ERROR: {ex}")
print(f"Tested {count} images.")

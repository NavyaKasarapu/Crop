import os
import sys
sys.path.insert(0, os.path.abspath("."))
from PIL import Image
import numpy as np
from backend.app.services.model_service import model_service

def predict_refined(image):
    # 1. Botanical domain & Quality validation
    valid, status_cat, validation_message, quality_warning, metrics = model_service._analyze_image_quality_and_domain(image)
    if not valid:
        if status_cat == "unsupported":
            return {
                "status_category": "unsupported",
                "crop": "Unknown image",
                "disease": "N/A",
                "condition": "Unsupported",
                "confidence": 0.0,
            }
        else:
            return {
                "status_category": "unknown",
                "crop": "Unknown",
                "disease": "N/A",
                "condition": "Unknown",
                "confidence": 0.0,
            }

    # 2. Multi-view inference: View 1 (full context) + View 2 (center crop)
    w, h = image.size
    min_dim = min(w, h)
    v1 = image.resize((224, 224), Image.Resampling.BILINEAR)
    v2 = image.crop(((w-min_dim)//2, (h-min_dim)//2, (w-min_dim)//2+min_dim, (h-min_dim)//2+min_dim)).resize((224, 224), Image.Resampling.BILINEAR)
    
    t1 = model_service._to_tensor(v1)
    t2 = model_service._to_tensor(v2)
    l1 = model_service.session.run(None, {"input": t1})[0][0]
    l2 = model_service.session.run(None, {"input": t2})[0][0]
    
    # Blend views
    raw_logits = 0.5 * (l1 + l2)
    z = raw_logits
    z_max = float(np.max(z))
    temp = max(model_service.temperature, 0.001)
    calibrated_z = z / temp
    max_c = np.max(calibrated_z)
    logsumexp = max_c + np.log(np.sum(np.exp(calibrated_z - max_c)))
    negative_energy = float(temp * logsumexp)
    
    exp_z = np.exp(calibrated_z - max_c)
    probs = exp_z / np.sum(exp_z)
    entropy = float(-np.sum(probs * np.log2(probs + 1e-12)))
    
    top_indices = np.argsort(probs)[::-1][:2]
    top1_idx = int(top_indices[0])
    top1_prob = float(probs[top1_idx])
    top2_prob = float(probs[top_indices[1]]) if len(top_indices) > 1 else 0.0
    
    raw_conf = top1_prob * 100.0
    raw_gap = (top1_prob - top2_prob) * 100.0
    
    predicted_class = model_service.class_names[top1_idx]
    predicted_crop, predicted_disease = model_service._parse_class_name(predicted_class)
    
    aspect_ratio = max(w, h) / max(1, min(w, h))

    # Check 1: Extreme OOD / Non-plant artifacts
    if negative_energy < 2.5 or z_max < 1.8:
        return {
            "status_category": "unsupported",
            "crop": "Unknown image",
            "disease": "N/A",
            "condition": "Unsupported",
            "confidence": round(raw_conf, 1),
        }

    # Check 2: Monocot grass / Rice guard
    # Rice blights and non-corn grass leaves produce weak Corn activations, or long blade aspect ratios with moderate conf
    if predicted_crop == "Corn":
        if z_max < 3.5 or raw_gap < 5.0 or (aspect_ratio > 2.6 and raw_conf < 70.0):
            return {
                "status_category": "unsupported",
                "crop": "Unsupported crop",
                "disease": "N/A",
                "condition": "Unsupported",
                "confidence": round(raw_conf, 1),
            }

    # Check 3: Strawberry guard (prevent elongated grass blades or weeds like rice brown spot mapping to strawberry)
    if predicted_crop == "Strawberry":
        if negative_energy < 3.4 or z_max < 2.8 or aspect_ratio > 2.2:
            return {
                "status_category": "unsupported",
                "crop": "Unsupported crop",
                "disease": "N/A",
                "condition": "Unsupported",
                "confidence": round(raw_conf, 1),
            }

    # Check 4: General OOD plant
    if negative_energy < 2.8 or z_max < 2.2:
        return {
            "status_category": "unsupported",
            "crop": "Unsupported crop",
            "disease": "N/A",
            "condition": "Unsupported",
            "confidence": round(raw_conf, 1),
        }

    # Check 5: Confident diagnosis vs Uncertain diagnosis for Supported Crop
    # If confidence is clear, declare disease
    is_confident = (raw_conf >= 45.0 and raw_gap >= 6.0 and entropy <= 2.3 and z_max >= 3.0) or (raw_conf >= 60.0 and raw_gap >= 8.0)
    
    if is_confident:
        is_healthy = predicted_disease.lower() == "healthy"
        return {
            "status_category": "supported_healthy" if is_healthy else "supported_diseased",
            "crop": predicted_crop,
            "disease": "Healthy" if is_healthy else predicted_disease,
            "condition": "Healthy" if is_healthy else "Disease Detected",
            "confidence": round(raw_conf, 1),
        }
    else:
        # Supported crop, but disease is uncertain
        return {
            "status_category": "uncertain",
            "crop": predicted_crop,
            "disease": "Unable to identify confidently",
            "condition": "Unable to identify confidently",
            "confidence": round(raw_conf, 1),
        }

if __name__ == "__main__":
    print("--- 1. Testing Rice Images ---")
    rice_dir = "data/test_rice"
    all_rice_rejected = True
    for f in os.listdir(rice_dir):
        im = Image.open(os.path.join(rice_dir, f)).convert("RGB")
        res = predict_refined(im)
        print(f"Rice {f:35s} -> status: {res['status_category']:12s} | crop: {res['crop']:16s} | dis: {res['disease']}")
        if res["status_category"] != "unsupported" or res["crop"] != "Unsupported crop":
            all_rice_rejected = False
    assert all_rice_rejected, "All rice must be rejected as Unsupported crop!"
    print("[OK] All rice images rejected as Unsupported crop!\n")

    print("--- 2. Testing Real-World Supported Images (Multiple Leaves & Background) ---")
    test_paths = [
        'data/plantdoc_extracted/test/Corn leaf blight/02c.jpg',
        'data/plantdoc_extracted/test/Corn leaf blight/0796.20graylssymt.jpg',
        'data/plantdoc_extracted/test/Corn Gray leaf spot/IMG_42231.jpg',
        'data/plantdoc_extracted/test/Corn rust leaf/0796.39maizerust.jpg',
        'data/plantdoc_extracted/test/Soyabean leaf/07feb_ma_sbr3.JPG.jpg',
        'data/plantdoc_extracted/test/grape leaf/0000.jpg',
        'data/plantdoc_extracted/test/Tomato leaf late blight/110822-206-Tomato-blight.jpg',
        'data/plantdoc_extracted/test/Tomato Septoria leaf spot/2septoria-tomato.jpg',
        'data/plantdoc_extracted/test/Tomato leaf/1684.jpg',
    ]
    for p in test_paths:
        if os.path.exists(p):
            im = Image.open(p).convert("RGB")
            res = predict_refined(im)
            print(f"{os.path.basename(p):35s} -> status: {res['status_category']:18s} | crop: {res['crop']:10s} | dis: {res['disease']}")
            assert res["crop"] != "Unsupported crop", f"{p} should NOT be unsupported!"
    print("\n[OK] ALL VERIFICATIONS PASSED!")

import sys
from pathlib import Path
import numpy as np
from PIL import Image
import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LLRL_ROOT = PROJECT_ROOT / "llrl_temp"
MODEL_PATH = PROJECT_ROOT / "backend" / "severity_model" / "best-HLFA-Net.pth"

if str(LLRL_ROOT) not in sys.path and LLRL_ROOT.exists():
    sys.path.insert(0, str(LLRL_ROOT))

CLASS_ORDER = [0, 1, 3, 5, 7, 9]  # LLRL class codes: 0 (healthy), 1 (low <10%), 3 (10-25%), 5 (25-50%), 7 (50-75%), 9 (>75%)
SUPPORTED_LLRL_CROPS = {"apple", "potato", "tomato"}


class SeverityService:
    def __init__(self):
        self.llrl_model = None
        self.llrl_available = False
        self._check_llrl()

    def _check_llrl(self):
        try:
            if MODEL_PATH.exists() and LLRL_ROOT.exists():
                from model.train import Trainer
                import torch
                model = Trainer("small", "classifier", 6)
                checkpoint = torch.load(MODEL_PATH, map_location="cpu", weights_only=False)
                model.load_state_dict(checkpoint, strict=False)
                model.eval()
                self.llrl_model = model
                self.llrl_available = True
                print("[SeverityService] LLRL HLFA-Net severity model loaded successfully.")
        except Exception as exc:
            self.llrl_available = False
            self.llrl_model = None
            print(f"[SeverityService] LLRL model not loaded ({exc}). Using CV lesion analysis.")

    def _estimate_leaf_affected_area(self, image: Image.Image):
        """
        Calculates honest lesion / necrotic area percentage using Computer Vision color segmentation.
        Completely separate from model classification confidence.
        """
        # Convert to BGR for OpenCV
        rgb = np.array(image.convert("RGB"))
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

        # 1. Mask for leaf tissue (green, yellowish-green, dry foliage)
        # H: 15-95 covers yellow-green, true green, and yellowish plant material
        # S: 20-255 filters out neutral/white/gray background
        # V: 25-250 filters out very dark shadows and specular highlights
        leaf_mask1 = cv2.inRange(hsv, np.array([15, 20, 25]), np.array([95, 255, 250]))
        # Also capture darker brown leaf margins and patches
        leaf_mask2 = cv2.inRange(hsv, np.array([5, 30, 25]), np.array([15, 255, 200]))
        leaf_mask = cv2.bitwise_or(leaf_mask1, leaf_mask2)

        leaf_pixel_count = int(cv2.countNonZero(leaf_mask))
        total_pixels = image.width * image.height

        if leaf_pixel_count < 200:
            # Fallback if leaf mask didn't isolate well
            leaf_pixel_count = total_pixels
            leaf_mask = np.ones((image.height, image.width), dtype=np.uint8) * 255

        # 2. Mask for diseased / lesion spots (necrotic brown, dark spots, chlorotic yellow patches)
        # Necrotic / dark lesions
        necrotic_mask = cv2.inRange(hsv, np.array([0, 30, 20]), np.array([22, 255, 140]))
        # Yellow chlorosis lesions
        chlorosis_mask = cv2.inRange(hsv, np.array([20, 75, 80]), np.array([36, 255, 255]))
        # Powdery mildew / whitish mold patches
        powdery_mask = cv2.inRange(hsv, np.array([0, 0, 170]), np.array([180, 50, 255]))

        combined_lesions = cv2.bitwise_or(necrotic_mask, chlorosis_mask)
        combined_lesions = cv2.bitwise_or(combined_lesions, powdery_mask)

        # Only count lesions that fall WITHIN the leaf area
        lesion_on_leaf = cv2.bitwise_and(combined_lesions, combined_lesions, mask=leaf_mask)
        lesion_pixel_count = int(cv2.countNonZero(lesion_on_leaf))

        ratio = (lesion_pixel_count / max(leaf_pixel_count, 1)) * 100.0
        # Smooth and bound to sensible realistic range
        ratio = max(1.5, min(85.0, ratio))
        return round(ratio, 1)

    def estimate(self, image: Image.Image, crop: str, condition: str):
        """
        Estimate severity, affected area, and health score based on image analysis.
        """
        cond_lower = condition.lower()

        if "healthy" in cond_lower:
            return {
                "severity": "None",
                "affected_area": "0%",
                "affected_area_percentage": 0.0,
                "health_score": 100,
                "method": "Healthy Leaf Baseline",
                "is_estimated": False,
                "details": "No disease lesions detected on healthy foliage.",
            }

        if "unknown" in cond_lower or "unable" in cond_lower or "unsupported" in cond_lower:
            return {
                "severity": "Unknown",
                "affected_area": "Unable to determine",
                "affected_area_percentage": None,
                "health_score": None,
                "method": "N/A",
                "is_estimated": False,
                "details": "Severity cannot be assessed for unverified plant image.",
            }

        # Disease detected:
        crop_clean = crop.strip().lower()
        cv_affected_ratio = self._estimate_leaf_affected_area(image)

        llrl_severity_code = None
        method_name = "Estimated (Computer Vision Leaf Area Analysis)"

        # Check if LLRL model can run for apple, potato, tomato
        if self.llrl_available and crop_clean in SUPPORTED_LLRL_CROPS:
            try:
                import torch
                from torchvision import transforms
                t = transforms.Compose([
                    transforms.Resize(256),
                    transforms.CenterCrop(224),
                    transforms.ToTensor(),
                    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
                ])
                tensor = t(image.convert("RGB")).unsqueeze(0)
                with torch.no_grad():
                    out = self.llrl_model(tensor, tensor)
                    pred_idx = int(torch.argmax(out, dim=1).item())
                    llrl_severity_code = CLASS_ORDER[pred_idx]
                    method_name = "Estimated (LLRL HLFA-Net + Lesion Analysis)"
            except Exception as e:
                print(f"[SeverityService] LLRL inference failed: {e}")

        # Map to Low / Medium / High
        if llrl_severity_code is not None:
            if llrl_severity_code <= 1:
                severity = "Low"
            elif llrl_severity_code <= 5:
                severity = "Medium"
            else:
                severity = "High"
        else:
            if cv_affected_ratio < 12.0:
                severity = "Low"
            elif cv_affected_ratio < 28.0:
                severity = "Medium"
            else:
                severity = "High"

        health_score = max(5, min(95, int(round(100 - cv_affected_ratio))))

        return {
            "severity": severity,
            "affected_area": f"{cv_affected_ratio}%",
            "affected_area_percentage": cv_affected_ratio,
            "health_score": health_score,
            "method": method_name,
            "is_estimated": True,
            "details": f"Estimated affected surface: {cv_affected_ratio}%. Assessment method: {method_name}.",
        }

severity_service = SeverityService()
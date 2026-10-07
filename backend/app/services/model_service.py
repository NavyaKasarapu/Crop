import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageStat
import onnxruntime as ort

class ModelService:
    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[3]

        # Candidates for ONNX model
        candidate_onnx_paths = [
            self.project_root / "model" / "artifacts" / "model.onnx",
            self.project_root / "backend" / "model" / "artifacts" / "model.onnx",
        ]

        # Candidates for labels
        candidate_label_paths = [
            self.project_root / "model" / "artifacts" / "labels.json",
            self.project_root / "backend" / "model" / "artifacts" / "labels.json",
            self.project_root / "backend" / "model" / "class_names.json",
        ]

        # Candidates for temperature calibration
        candidate_temp_paths = [
            self.project_root / "backend" / "model" / "confidence_temperature.json",
            self.project_root / "model" / "artifacts" / "confidence_temperature.json",
        ]

        self.model_path = next((p for p in candidate_onnx_paths if p.exists()), None)
        self.class_names_path = next((p for p in candidate_label_paths if p.exists()), None)
        self.temperature_path = next((p for p in candidate_temp_paths if p.exists()), None)

        self.minimum_confidence = 48.0
        self.minimum_probability_gap = 6.0
        self.minimum_image_width = 100
        self.minimum_image_height = 100

        self.class_names = []
        self.temperature = 1.0
        self.session = None
        self.is_available = False
        self.unavailable_reason = ""

        self._initialize_model()

    def _initialize_model(self):
        """Safely load ONNX model and metadata without crashing if files are missing."""
        if not self.model_path or not self.class_names_path:
            self.is_available = False
            self.unavailable_reason = "AI model is currently unavailable. Please train/export the model first."
            print(f"[ModelService] WARNING: {self.unavailable_reason}")
            return

        try:
            with open(self.class_names_path, "r", encoding="utf-8") as f:
                self.class_names = json.load(f)

            if not isinstance(self.class_names, list) or len(self.class_names) == 0:
                raise ValueError("Labels file is empty or corrupted.")

            if self.temperature_path and self.temperature_path.exists():
                try:
                    with open(self.temperature_path, "r", encoding="utf-8") as f:
                        t_data = json.load(f)
                        self.temperature = float(t_data.get("temperature", 1.0))
                        if self.temperature <= 0:
                            self.temperature = 1.0
                except Exception:
                    self.temperature = 1.0

            # Create ONNX runtime session
            opts = ort.SessionOptions()
            opts.intra_op_num_threads = 2
            opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            self.session = ort.InferenceSession(
                str(self.model_path),
                sess_options=opts,
                providers=["CPUExecutionProvider"]
            )
            self.is_available = True
            print(f"[ModelService] Successfully loaded ONNX model from {self.model_path} with {len(self.class_names)} classes.")
        except Exception as exc:
            self.is_available = False
            self.unavailable_reason = f"Failed to load AI model: {str(exc)}"
            print(f"[ModelService] ERROR: {self.unavailable_reason}")

    def _sanitize_image(self, image: Image.Image) -> Image.Image:
        """Apply EXIF orientation and composite alpha transparency onto neutral white."""
        try:
            from PIL import ImageOps
            image = ImageOps.exif_transpose(image)
        except Exception:
            pass

        if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
            rgba = image.convert("RGBA")
            bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
            image = Image.alpha_composite(bg, rgba).convert("RGB")
        else:
            image = image.convert("RGB")

        return image

    def _validate_image(self, image: Image.Image):
        if image is None:
            return False, "No image was provided."

        width, height = image.size
        if width < self.minimum_image_width or height < self.minimum_image_height:
            return False, f"The image is too small ({width}x{height}). Minimum required is 100x100 pixels."

        rgb_image = image.convert("RGB")
        stat = ImageStat.Stat(rgb_image)
        brightness = sum(stat.mean) / len(stat.mean)
        stddev = sum(stat.stddev) / len(stat.stddev)

        if brightness < 20:
            return False, "The image is too dark. Please take the photo in better lighting."
        if brightness > 245:
            return False, "The image is overexposed. Please take a clearer photo with less glare."
        if stddev < 12.0:
            return False, "The image appears blank or lacks sufficient visual detail. Please upload a clear photo of a crop leaf."

        return True, ""

    def _to_tensor(self, img: Image.Image) -> np.ndarray:
        """Preprocess PIL Image into normalized float32 tensor [1, 3, 224, 224]."""
        arr = np.array(img, dtype=np.float32) / 255.0  # (224, 224, 3)
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        arr = ((arr - mean) / std).astype(np.float32)
        arr = np.transpose(arr, (2, 0, 1))  # (3, 224, 224)
        arr = np.expand_dims(arr, axis=0)   # (1, 3, 224, 224)
        return arr

    def _parse_class_name(self, predicted_class: str):
        crop_clean_map = {
            "Apple": "Apple",
            "Blueberry": "Blueberry",
            "Cherry_(including_sour)": "Cherry",
            "Corn_(maize)": "Corn",
            "Grape": "Grape",
            "Orange": "Orange",
            "Peach": "Peach",
            "Pepper,_bell": "Bell Pepper",
            "Potato": "Potato",
            "Raspberry": "Raspberry",
            "Soybean": "Soybean",
            "Squash": "Squash",
            "Strawberry": "Strawberry",
            "Tomato": "Tomato",
        }

        if "___" in predicted_class:
            raw_crop, raw_disease = predicted_class.split("___", 1)
        else:
            raw_crop = predicted_class
            raw_disease = "healthy"

        crop = crop_clean_map.get(raw_crop, raw_crop.replace("_", " ").strip())
        disease = raw_disease.replace("_", " ").strip()
        disease = " ".join(disease.split())
        return crop, disease

    def _assess_reliability(self, confidence: float, probability_gap: float):
        if confidence < self.minimum_confidence or probability_gap < self.minimum_probability_gap:
            return "Low", "The model could not identify a sufficiently reliable class for this image."
        if confidence < 75.0:
            return "Moderate", "The model favors this class, but the result should be treated as an AI-assisted estimate."
        return "High", "The model strongly favors this class based on leaf pattern matching."

    def predict(self, image: Image.Image):
        if not self.is_available or self.session is None:
            raise RuntimeError(self.unavailable_reason or "AI model is currently unavailable. Please train/export the model first.")

        # 1. Sanitize image (EXIF orientation + alpha composite)
        image = self._sanitize_image(image)

        # 2. Quality validation
        valid, validation_message = self._validate_image(image)
        if not valid:
            return {
                "crop": "Unsupported Image / Crop",
                "disease": "Unsupported Image / Crop",
                "condition": "Unsupported",
                "confidence": 0.0,
                "probability_gap": 0.0,
                "reliability": "Low",
                "reliability_message": validation_message,
                "health_status": "Unsupported",
                "unsupported": True,
                "predicted_class": None,
            }

        # 3. View 1: Direct full-context resize to 224x224 (matches dataset eval)
        v1 = image.resize((224, 224), Image.Resampling.BILINEAR)
        tensor1 = self._to_tensor(v1)
        out1 = self.session.run(None, {"input": tensor1})[0][0]
        calibrated1 = out1 / max(self.temperature, 0.001)
        exp1 = np.exp(calibrated1 - np.max(calibrated1))
        prob1 = exp1 / np.sum(exp1)

        w, h = image.size
        aspect_ratio = w / h if h > 0 else 1.0

        # View 2: If image is non-square (typical phone photo), also evaluate aspect-ratio preserved center crop
        if aspect_ratio < 0.85 or aspect_ratio > 1.18:
            if w < h:
                nw = 256
                nh = int(h * (256 / w))
            else:
                nh = 256
                nw = int(w * (256 / h))
            v2 = image.resize((nw, nh), Image.Resampling.BILINEAR)
            left = (nw - 224) // 2
            top = (nh - 224) // 2
            v2 = v2.crop((left, top, left + 224, top + 224))
            tensor2 = self._to_tensor(v2)
            out2 = self.session.run(None, {"input": tensor2})[0][0]
            calibrated2 = out2 / max(self.temperature, 0.001)
            exp2 = np.exp(calibrated2 - np.max(calibrated2))
            prob2 = exp2 / np.sum(exp2)

            top1_1 = float(np.max(prob1))
            top1_2 = float(np.max(prob2))
            if top1_2 > top1_1 + 0.15:
                probabilities = prob2
            elif top1_1 > top1_2 + 0.15:
                probabilities = prob1
            else:
                probabilities = 0.5 * (prob1 + prob2)
        else:
            probabilities = prob1

        # Top 2
        top_indices = np.argsort(probabilities)[::-1][:2]
        top1_idx = int(top_indices[0])
        top1_prob = float(probabilities[top1_idx])
        top2_prob = float(probabilities[top_indices[1]]) if len(top_indices) > 1 else 0.0

        # Honest confidence calculation
        # If the probability is not mathematically 1.0, format to preserve true decimal precision and avoid prematurely rounding up to 100.0%
        raw_conf = top1_prob * 100.0
        if top1_prob < 1.0 and raw_conf >= 99.995:
            conf_display = 99.99
        else:
            conf_display = round(raw_conf, 2)

        raw_gap = (top1_prob - top2_prob) * 100.0
        gap_display = round(raw_gap, 2)
        predicted_class = self.class_names[top1_idx]

        reliability, reliability_message = self._assess_reliability(raw_conf, raw_gap)

        # Gating: low confidence or competing classes -> abstain to Unsupported Image / Crop
        if raw_conf < self.minimum_confidence or raw_gap < self.minimum_probability_gap:
            return {
                "crop": "Unsupported Image / Crop",
                "disease": "Unsupported Image / Crop",
                "condition": "Unsupported",
                "confidence": conf_display,
                "probability_gap": gap_display,
                "reliability": "Low",
                "reliability_message": (
                    "This image does not match any of the 14 supported crops in the trained dataset with high confidence. "
                    "Please upload a clear, focused photo of a crop leaf."
                ),
                "health_status": "Unsupported",
                "unsupported": True,
                "predicted_class": None,
            }

        crop, disease = self._parse_class_name(predicted_class)

        if disease.lower() == "healthy":
            condition = "Healthy"
            health_status = "Healthy"
            disease_display = "Healthy"
        else:
            condition = "Disease Detected"
            health_status = "Disease Detected"
            disease_display = disease

        return {
            "crop": crop,
            "disease": disease_display,
            "condition": condition,
            "confidence": conf_display,
            "probability_gap": gap_display,
            "reliability": reliability,
            "reliability_message": reliability_message,
            "health_status": health_status,
            "unsupported": False,
            "predicted_class": predicted_class,
        }

model_service = ModelService()
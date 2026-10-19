import json
from pathlib import Path
from typing import Optional
import numpy as np
import onnxruntime as ort
from PIL import Image, ImageStat

class ModelService:
    CONFIDENCE_LIMITATION_EXPLANATION = (
        "Classification confidence reflects algorithmic similarity to the visual patterns in our trained "
        "crop-disease categories. It is not an absolute clinical guarantee and cannot diagnose plant species "
        "or pathogens outside the trained domain. Field confirmation by an agronomist is recommended for critical decisions."
    )

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

        self.minimum_confidence = 50.0
        self.minimum_probability_gap = 7.0
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

    @property
    def supported_crops(self):
        """Dynamic list of unique crop names extracted from the actual loaded model classes."""
        return [c["name"] for c in self.get_supported_crops()]

    def get_supported_crops(self):
        """
        Dynamically extracts unique crop names, condition counts, and diseases directly
        from the loaded model class names (labels.json). Deduplicates healthy and diseased
        classes so each crop appears only once.
        """
        if not self.class_names:
            return []

        crop_icons = {
            "Apple": "🍎",
            "Blueberry": "🫐",
            "Cherry": "🍒",
            "Corn": "🌽",
            "Grape": "🍇",
            "Orange": "🍊",
            "Peach": "🍑",
            "Bell Pepper": "🫑",
            "Potato": "🥔",
            "Raspberry": "🫐",
            "Soybean": "🌱",
            "Squash": "🎃",
            "Strawberry": "🍓",
            "Tomato": "🍅",
        }

        crops_map = {}
        for class_name in self.class_names:
            crop, disease = self._parse_class_name(class_name)
            if crop not in crops_map:
                crops_map[crop] = {
                    "name": crop,
                    "classes": [],
                    "has_healthy": False,
                    "diseases": []
                }
            crops_map[crop]["classes"].append(class_name)
            if disease.lower() == "healthy":
                crops_map[crop]["has_healthy"] = True
            else:
                if disease not in crops_map[crop]["diseases"]:
                    crops_map[crop]["diseases"].append(disease)

        EXACT_CROP_ORDER = [
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

        result = []
        # Add crops in the exact user-specified order if present in model classes
        for crop_name, default_icon in EXACT_CROP_ORDER:
            if crop_name in crops_map:
                info = crops_map[crop_name]
                result.append({
                    "name": crop_name,
                    "icon": crop_icons.get(crop_name, default_icon),
                    "total_classes": len(info["classes"]),
                    "healthy_supported": info["has_healthy"],
                    "disease_count": len(info["diseases"]),
                    "diseases": info["diseases"],
                    "classes": info["classes"]
                })

        # Append any other trained crops if present (to never hide trained classes)
        for crop_name in sorted(crops_map.keys()):
            if not any(c["name"] == crop_name for c in result):
                info = crops_map[crop_name]
                result.append({
                    "name": crop_name,
                    "icon": crop_icons.get(crop_name, "🌿"),
                    "total_classes": len(info["classes"]),
                    "healthy_supported": info["has_healthy"],
                    "disease_count": len(info["diseases"]),
                    "diseases": info["diseases"],
                    "classes": info["classes"]
                })
        return result

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

    def _analyze_image_quality_and_domain(self, image: Image.Image):
        """
        Botanical domain & image quality gating:
        1. Checks dimensions, lighting, contrast
        2. Detects severe blur via Laplacian variance on standardized 256x256 grayscale
        3. Segments plant foliage / leaf matter via HSV and ExG to reject non-leaf / unrelated images
        """
        if image is None:
            return False, "unsupported", "No image was provided.", None, {}

        w, h = image.size
        if w < self.minimum_image_width or h < self.minimum_image_height:
            return False, "unknown", f"The image is too small ({w}x{h}). Minimum required is 100x100 pixels.", None, {}

        rgb = np.array(image.convert("RGB"), dtype=np.uint8)
        gray = (0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]).astype(np.float32)
        brightness = float(np.mean(gray))
        stddev = float(np.std(gray))

        # 1. Blur detection via Laplacian variance on standardized 256x256
        scale = 256.0 / max(w, h)
        nw, nh = max(4, int(w * scale)), max(4, int(h * scale))
        im_small = image.convert("L").resize((nw, nh), Image.Resampling.BILINEAR)
        gray_small = np.array(im_small, dtype=np.float32)
        lap = (
            -4.0 * gray_small[1:-1, 1:-1]
            + gray_small[:-2, 1:-1]
            + gray_small[2:, 1:-1]
            + gray_small[1:-1, :-2]
            + gray_small[1:-1, 2:]
        )
        blur_var = float(np.var(lap))

        # 2. Foliage & Botanical domain check
        r = rgb[:, :, 0].astype(np.float32)
        g = rgb[:, :, 1].astype(np.float32)
        b = rgb[:, :, 2].astype(np.float32)
        exg = 2.0 * g - r - b  # Excess Green Index

        hsv = np.array(image.convert("HSV"), dtype=np.uint8)
        hue = hsv[:, :, 0]  # PIL Hue: 0-255 (0-360 deg)
        sat = hsv[:, :, 1]
        val = hsv[:, :, 2]

        # Green leaf foliage (approx 30 deg to 175 deg -> 21 to 124 in PIL scale)
        green_mask = (hue >= 20) & (hue <= 126) & (sat >= 20) & (val >= 20)
        # Chlorotic/yellow tissue (approx 18 to 38 deg -> 13 to 27 in PIL scale)
        yellow_mask = (hue >= 11) & (hue <= 28) & (sat >= 20) & (val >= 25)
        # Necrotic / brown / tan fungal lesions (e.g. leaf scorch, blights)
        lesion_mask = (hue >= 3) & (hue <= 20) & (sat >= 15) & (val >= 15) & (val <= 215)
        # Reddish-purple scorch / anthocyanin foliar pigmentation (e.g. strawberry leaf scorch)
        purple_red_mask = ((hue >= 215) | (hue <= 10)) & (sat >= 20) & (val >= 20) & (val <= 215)
        # Vegetative index
        exg_mask = (exg > 5.0) & (sat >= 15) & (val >= 15)

        plant_mask = green_mask | yellow_mask | lesion_mask | purple_red_mask | exg_mask
        foliage_ratio = float(np.mean(plant_mask))

        metrics = {
            "brightness": round(brightness, 1),
            "stddev": round(stddev, 1),
            "blur_var": round(blur_var, 1),
            "foliage_ratio": round(foliage_ratio, 3),
        }

        # Botanical domain rejection: unrelated non-leaf images
        # 0.05 threshold allows field close-ups (e.g. strawberry on soil/mulch) while rejecting pure non-plants
        if foliage_ratio < 0.05:
            return (
                False,
                "unsupported",
                "No recognizable plant leaf or foliage detected in the frame. The image appears to be an unrelated object or non-plant subject.",
                None,
                metrics
            )

        # Severe blur rejection
        # Calibrated on PlantDoc field images: threshold 8.0 rejects truly unusable blur
        if blur_var < 8.0:
            return (
                False,
                "unknown",
                "The photo is too blurry for an accurate foliar diagnosis. Please stabilize the camera and capture a sharp photo in focus.",
                "The photo is out of focus. Fine pathological symptoms cannot be resolved.",
                metrics
            )

        # Extreme lighting rejections
        if brightness < 20.0:
            return (
                False,
                "unknown",
                "The photo is too dark. Please take the photograph in bright, uniform daylight.",
                "The image is severely underexposed. Symptoms may be obscured by dark shadows.",
                metrics
            )

        if brightness > 244.0:
            return (
                False,
                "unknown",
                "The photo is overexposed. Glare and high brightness obscure leaf tissue details.",
                "The image is overexposed with highlight clipping.",
                metrics
            )

        if stddev < 10.0:
            return (
                False,
                "unknown",
                "The image appears blank or lacks sufficient visual contrast.",
                "Low contrast/uniform image.",
                metrics
            )

        # Suboptimal quality warnings (image is acceptable, but warning advises the user)
        # blur_var < 50 = ~10th percentile of real PlantDoc field images
        warning = None
        if blur_var < 50.0:
            warning = "Notice: The image has slight motion blur or soft focus, which may reduce diagnostic precision."
        elif brightness < 42.0:
            warning = "Notice: The image was taken in dim lighting. For best results, use direct daylight."

        return True, "valid", "", warning, metrics

    def _to_tensor(self, img: Image.Image) -> np.ndarray:
        """Preprocess PIL Image into normalized float32 tensor [1, 3, 224, 224]."""
        arr = np.array(img, dtype=np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        arr = ((arr - mean) / std).astype(np.float32)
        arr = np.transpose(arr, (2, 0, 1))
        arr = np.expand_dims(arr, axis=0)
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

    def _assess_reliability(self, confidence: float, probability_gap: float, entropy: float):
        if confidence < self.minimum_confidence or probability_gap < self.minimum_probability_gap or entropy > 2.2:
            return "Low", "The model could not identify a sufficiently reliable class for this image."
        if confidence < 75.0 or entropy > 1.5:
            return "Moderate", "The model favors this class, but the result should be treated as an AI-assisted estimate."
        return "High", "The model strongly favors this class based on leaf pattern matching."

    def predict(self, image: Image.Image, filename: Optional[str] = None):
        if not self.is_available or self.session is None:
            raise RuntimeError(
                self.unavailable_reason or "AI model is currently unavailable. Please train/export the model first."
            )

        # 1. Sanitize image (EXIF orientation + alpha composite onto white background)
        image = self._sanitize_image(image)

        # 2. Quality and botanical domain validation
        valid, status_cat, validation_message, quality_warning, metrics = self._analyze_image_quality_and_domain(image)
        if not valid:
            if status_cat == "unsupported":
                status_label = "Unknown image — non-plant or unrelated object detected."
                condition = "Unsupported"
                crop_name = "Unknown image"
                disease_name = "N/A"
                health_status = "Unsupported"
            else:
                status_label = "Image unclear — unable to analyze reliably."
                condition = "Unknown"
                crop_name = "Unknown"
                disease_name = "N/A"
                health_status = "Unknown"

            return {
                "status_category": status_cat,
                "status_label": status_label,
                "crop": crop_name,
                "disease": disease_name,
                "condition": condition,
                "confidence": 0.0,
                "probability_gap": 0.0,
                "reliability": "Low",
                "reliability_message": validation_message,
                "quality_warning": quality_warning or validation_message,
                "confidence_explanation": self.CONFIDENCE_LIMITATION_EXPLANATION,
                "health_status": health_status,
                "unsupported": True,
                "predicted_class": None,
                "diagnostic_metrics": metrics,
            }

        # 3. Model Inference: Multi-View Foliage Gating
        # View 1: Full context image resize
        v1 = image.resize((224, 224), Image.Resampling.BILINEAR)
        tensor1 = self._to_tensor(v1)
        raw_logits1 = self.session.run(None, {"input": tensor1})[0][0]

        w, h = image.size
        min_dim = min(w, h)

        # View 2: Center crop for aspect-ratio preservation
        left = (w - min_dim) // 2
        top = (h - min_dim) // 2
        v2 = image.crop((left, top, left + min_dim, top + min_dim)).resize((224, 224), Image.Resampling.BILINEAR)
        tensor2 = self._to_tensor(v2)
        raw_logits2 = self.session.run(None, {"input": tensor2})[0][0]

        # Blend views: gives robust representation for both full plant canopy and center foliage
        raw_logits = 0.5 * (raw_logits1 + raw_logits2)

        # 4. Out-of-Distribution (OOD) Metrics on Logits
        z = raw_logits
        z_max = float(np.max(z))
        temp = max(self.temperature, 0.001)

        # Free Energy Score: E(x) = -T * log(sum(exp(z_i / T)))
        calibrated_z = z / temp
        max_c = np.max(calibrated_z)
        logsumexp = max_c + np.log(np.sum(np.exp(calibrated_z - max_c)))
        negative_energy = float(temp * logsumexp)

        # Softmax probabilities
        exp_z = np.exp(calibrated_z - max_c)
        probabilities = exp_z / np.sum(exp_z)

        # Shannon Predictive Entropy
        entropy = float(-np.sum(probabilities * np.log2(probabilities + 1e-12)))

        # Top 2 predictions
        top_indices = np.argsort(probabilities)[::-1][:2]
        top1_idx = int(top_indices[0])
        top1_prob = float(probabilities[top1_idx])
        top2_prob = float(probabilities[top_indices[1]]) if len(top_indices) > 1 else 0.0

        raw_conf = top1_prob * 100.0
        conf_display = 99.99 if (top1_prob < 1.0 and raw_conf >= 99.995) else round(raw_conf, 2)

        raw_gap = (top1_prob - top2_prob) * 100.0
        gap_display = round(raw_gap, 2)
        predicted_class = self.class_names[top1_idx]
        predicted_crop, predicted_disease = self._parse_class_name(predicted_class)

        metrics.update({
            "energy_score": round(negative_energy, 2),
            "max_logit": round(z_max, 2),
            "entropy": round(entropy, 2),
        })

        supported_crops_list = ", ".join(self.supported_crops)
        aspect_ratio = max(w, h) / max(1, min(w, h))

        # 5. Non-Plant / Unrelated Object Rejection
        if negative_energy < 2.5 or z_max < 1.8:
            return {
                "status_category": "unsupported",
                "status_label": "Unknown image — non-plant or unrelated object detected.",
                "crop": "Unknown image",
                "disease": "N/A",
                "condition": "Unsupported",
                "confidence": conf_display,
                "probability_gap": gap_display,
                "reliability": "Low",
                "reliability_message": (
                    f"This image does not match any of the supported crop distributions in our trained model. "
                    f"Crop Disease AI only analyzes: {supported_crops_list}."
                ),
                "quality_warning": quality_warning,
                "confidence_explanation": self.CONFIDENCE_LIMITATION_EXPLANATION,
                "health_status": "Unsupported",
                "unsupported": True,
                "predicted_class": None,
                "diagnostic_metrics": metrics,
            }

        # 6. Monocot / Cereal Leaf Domain Rejection (Rice & Non-Corn Grasses)
        # Rice blights and wild grass leaves produce weak Corn activations, or long blade aspect ratios with moderate conf
        if predicted_crop == "Corn":
            if z_max < 3.5 or raw_gap < 5.0 or (aspect_ratio > 2.6 and raw_conf < 70.0):
                return {
                    "status_category": "unsupported",
                    "status_label": "Unsupported crop — foliar pattern resembles unsupported cereal or grass species (such as rice).",
                    "crop": "Unsupported crop",
                    "disease": "N/A",
                    "condition": "Unsupported",
                    "confidence": conf_display,
                    "probability_gap": gap_display,
                    "reliability": "Low",
                    "reliability_message": (
                        "The model could not verify this as a supported corn crop. "
                        "Rice, wheat, and other non-supported cereal/grass leaves visually resemble corn blights "
                        "but are not supported by this model."
                    ),
                    "quality_warning": "Foliar pattern resembles unsupported cereal/grass species (such as rice).",
                    "confidence_explanation": self.CONFIDENCE_LIMITATION_EXPLANATION,
                    "health_status": "Unsupported",
                    "unsupported": True,
                    "predicted_class": None,
                    "diagnostic_metrics": metrics,
                }

        # 7. Specialized Handling for Strawberry (Supported Crop)
        # Prevent elongated grass blades (aspect_ratio > 2.2) or weeds from mapping to strawberry
        if predicted_crop == "Strawberry":
            if negative_energy < 3.4 or z_max < 2.8 or aspect_ratio > 2.2:
                return {
                    "status_category": "unsupported",
                    "status_label": "Unsupported crop — this species is not among the 14 supported crops.",
                    "crop": "Unsupported crop",
                    "disease": "N/A",
                    "condition": "Unsupported",
                    "confidence": conf_display,
                    "probability_gap": gap_display,
                    "reliability": "Low",
                    "reliability_message": (
                        f"This leaf image does not match any of the supported crop distributions in our trained model. "
                        f"Crop Disease AI only analyzes: {supported_crops_list}."
                    ),
                    "quality_warning": quality_warning,
                    "confidence_explanation": self.CONFIDENCE_LIMITATION_EXPLANATION,
                    "health_status": "Unsupported",
                    "unsupported": True,
                    "predicted_class": None,
                    "diagnostic_metrics": metrics,
                }

        # 8. General Out-of-Distribution Gating for Non-Supported Flora
        if negative_energy < 2.8 or z_max < 2.2:
            return {
                "status_category": "unsupported",
                "status_label": "Unsupported crop — this species is not among the 14 supported crops.",
                "crop": "Unsupported crop",
                "disease": "N/A",
                "condition": "Unsupported",
                "confidence": conf_display,
                "probability_gap": gap_display,
                "reliability": "Low",
                "reliability_message": (
                    f"This leaf image does not match any of the supported crop distributions in our trained model. "
                    f"Crop Disease AI only analyzes: {supported_crops_list}."
                ),
                "quality_warning": quality_warning,
                "confidence_explanation": self.CONFIDENCE_LIMITATION_EXPLANATION,
                "health_status": "Unsupported",
                "unsupported": True,
                "predicted_class": None,
                "diagnostic_metrics": metrics,
            }

        # 9. Confident Diagnosis vs Uncertain Diagnosis for Supported Crops
        # Real-world photos with multiple leaves, overlapping canopy, or subtle lesions
        # are acknowledged as supported crops, but guarded against false disease guesses!
        is_confident = (raw_conf >= 45.0 and raw_gap >= 6.0 and entropy <= 2.3 and z_max >= 3.0) or (raw_conf >= 60.0 and raw_gap >= 8.0)

        if not is_confident:
            return {
                "status_category": "uncertain",
                "status_label": f"Supported crop ({predicted_crop}) identified, but disease is uncertain.",
                "crop": predicted_crop,
                "disease": "Unable to identify confidently",
                "condition": "Unable to identify confidently",
                "confidence": conf_display,
                "probability_gap": gap_display,
                "reliability": "Low",
                "reliability_message": (
                    f"The leaf appears to be {predicted_crop}, but the specific disease condition cannot be confirmed with high certainty "
                    f"(common with multiple leaves, overlapping foliage, or early-stage lesions). "
                    f"Please take a closer photo of a single affected leaf in daylight."
                ),
                "quality_warning": quality_warning or "Multiple leaves, complex background, or subtle foliar lesions detected.",
                "confidence_explanation": self.CONFIDENCE_LIMITATION_EXPLANATION,
                "health_status": "Unable to determine",
                "unsupported": False,
                "predicted_class": None,
                "diagnostic_metrics": metrics,
            }

        # 10. In-Distribution Confident Supported Prediction
        is_healthy = predicted_disease.lower() == "healthy"

        if is_healthy:
            status_category = "supported_healthy"
            status_label = "Supported crop — healthy"
            condition = "Healthy"
            health_status = "Healthy"
            disease_display = "Healthy"
        else:
            status_category = "supported_diseased"
            status_label = "Supported crop — disease detected"
            condition = "Disease Detected"
            health_status = "Disease Detected"
            disease_display = predicted_disease

        reliability, reliability_message = self._assess_reliability(raw_conf, raw_gap, entropy)

        return {
            "status_category": status_category,
            "status_label": status_label,
            "crop": predicted_crop,
            "disease": disease_display,
            "condition": condition,
            "confidence": conf_display,
            "probability_gap": gap_display,
            "reliability": reliability,
            "reliability_message": reliability_message,
            "quality_warning": quality_warning,
            "confidence_explanation": self.CONFIDENCE_LIMITATION_EXPLANATION,
            "health_status": health_status,
            "unsupported": False,
            "predicted_class": predicted_class,
            "diagnostic_metrics": metrics,
        }

model_service = ModelService()
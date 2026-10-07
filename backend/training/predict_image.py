import sys
import json
from pathlib import Path

import torch
import torch.nn as nn
from PIL import Image
from torchvision.models import mobilenet_v3_small, MobileNet_V3_Small_Weights


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = Path("backend/model/crop_disease_mobilenetv3.pth")
CLASS_NAMES_PATH = Path("backend/model/class_names.json")

IMAGE_SIZE = 224

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ============================================================
# LOAD CLASS NAMES
# ============================================================

with open(CLASS_NAMES_PATH, "r", encoding="utf-8") as f:
    class_names = json.load(f)


# ============================================================
# LOAD MODEL
# ============================================================

print("=" * 70)
print("Crop Disease AI - Single Image Prediction")
print("=" * 70)

print(f"\nDevice: {device}")
print("Loading MobileNetV3-Small...")

model = mobilenet_v3_small(
    weights=MobileNet_V3_Small_Weights.DEFAULT
)

input_features = model.classifier[3].in_features

model.classifier[3] = nn.Linear(
    input_features,
    len(class_names)
)

checkpoint = torch.load(
    MODEL_PATH,
    map_location=device,
    weights_only=True
)

model.load_state_dict(checkpoint)
model.to(device)
model.eval()

print("Model loaded successfully.")
print(f"Number of classes: {len(class_names)}")


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

weights = MobileNet_V3_Small_Weights.DEFAULT

transform = weights.transforms()


# ============================================================
# IMAGE PATH
# ============================================================

if len(sys.argv) < 2:
    print("\nUsage:")
    print("python backend\\training\\predict_image.py <image_path>")
    print("\nExample:")
    print(
        "python backend\\training\\predict_image.py "
        "C:\\Users\\PC\\OneDrive\\Desktop\\crop\\test_leaf.jpg"
    )
    sys.exit(1)


image_path = Path(sys.argv[1])

if not image_path.exists():
    print(f"\nERROR: Image not found:")
    print(image_path)
    sys.exit(1)


# ============================================================
# LOAD IMAGE
# ============================================================

try:
    image = Image.open(image_path).convert("RGB")
except Exception as e:
    print(f"\nERROR: Could not open image: {e}")
    sys.exit(1)


print(f"\nImage: {image_path}")
print(f"Original size: {image.size}")


# ============================================================
# PREDICTION
# ============================================================

input_tensor = transform(image).unsqueeze(0).to(device)

with torch.no_grad():
    outputs = model(input_tensor)

    probabilities = torch.softmax(outputs, dim=1)

    confidence, predicted_index = torch.max(
        probabilities,
        dim=1
    )

predicted_index = predicted_index.item()
confidence = confidence.item() * 100

predicted_class = class_names[predicted_index]


# ============================================================
# PARSE CROP AND DISEASE
# ============================================================

if "___" in predicted_class:
    crop, disease = predicted_class.split("___", 1)
else:
    crop = predicted_class
    disease = "Unknown"


# Clean crop name
crop = crop.replace("_", " ")


# Clean disease name
disease = disease.replace("_", " ")
disease = disease.replace("  ", " ")


# ============================================================
# HEALTH STATUS
# ============================================================

if disease.lower() == "healthy":
    health_status = "Healthy"
    disease_display = "None detected"
else:
    health_status = "Disease Detected"
    disease_display = disease


# ============================================================
# DISPLAY RESULT
# ============================================================

print("\n" + "=" * 70)
print("PREDICTION RESULT")
print("=" * 70)

print(f"\nCrop:          {crop}")
print(f"Disease:       {disease_display}")
print(f"Confidence:    {confidence:.2f}%")
print(f"Health Status: {health_status}")

print("\n" + "=" * 70)
print("TOP 5 PREDICTIONS")
print("=" * 70)


top_values, top_indices = torch.topk(
    probabilities[0],
    k=5
)

for rank, (value, index) in enumerate(
    zip(top_values, top_indices),
    start=1
):
    class_name = class_names[index.item()]
    percentage = value.item() * 100

    print(
        f"{rank}. {class_name:<55} "
        f"{percentage:.2f}%"
    )

print("\n" + "=" * 70)
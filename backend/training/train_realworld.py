import sys
import os
import time
import json
import random
from pathlib import Path
from collections import Counter
from PIL import Image

import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from torchvision.models import mobilenet_v3_small, MobileNet_V3_Small_Weights

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

PLANTDOC_TO_PV = {
    "Apple leaf": "Apple___healthy",
    "Apple rust leaf": "Apple___Cedar_apple_rust",
    "Apple Scab Leaf": "Apple___Apple_scab",
    "Bell_pepper leaf": "Pepper,_bell___healthy",
    "Bell_pepper leaf spot": "Pepper,_bell___Bacterial_spot",
    "Blueberry leaf": "Blueberry___healthy",
    "Cherry leaf": "Cherry_(including_sour)___healthy",
    "Corn Gray leaf spot": "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn leaf blight": "Corn_(maize)___Northern_Leaf_Blight",
    "Corn rust leaf": "Corn_(maize)___Common_rust_",
    "Peach leaf": "Peach___healthy",
    "Potato leaf early blight": "Potato___Early_blight",
    "Potato leaf late blight": "Potato___Late_blight",
    "Raspberry leaf": "Raspberry___healthy",
    "Soyabean leaf": "Soybean___healthy",
    "Squash Powdery mildew leaf": "Squash___Powdery_mildew",
    "Strawberry leaf": "Strawberry___healthy",
    "Tomato Early blight leaf": "Tomato___Early_blight",
    "Tomato Septoria leaf spot": "Tomato___Septoria_leaf_spot",
    "Tomato leaf bacterial spot": "Tomato___Bacterial_spot",
    "Tomato leaf late blight": "Tomato___Late_blight",
    "Tomato leaf mosaic virus": "Tomato___Tomato_mosaic_virus",
    "Tomato leaf yellow virus": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato leaf": "Tomato___healthy",
    "Tomato mold leaf": "Tomato___Leaf_Mold",
    "Tomato two spotted spider mites leaf": "Tomato___Spider_mites Two-spotted_spider_mite",
    "grape leaf black rot": "Grape___Black_rot",
    "grape leaf": "Grape___healthy",
}

train_transforms = transforms.Compose([
    transforms.RandomResizedCrop(224, scale=(0.7, 1.0)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomRotation(degrees=15),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.05),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

eval_transforms = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

class CombinedCropDataset(Dataset):
    def __init__(self, samples, transform=None):
        self.samples = samples
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        try:
            with Image.open(path) as img:
                img = img.convert("RGB")
        except Exception:
            img = Image.new("RGB", (224, 224), (128, 128, 128))

        if self.transform:
            img = self.transform(img)
        return img, label

def load_class_mapping():
    labels_path = PROJECT_ROOT / "model" / "artifacts" / "labels.json"
    with open(labels_path, "r", encoding="utf-8") as f:
        class_names = json.load(f)
    class_to_idx = {name: idx for idx, name in enumerate(class_names)}
    return class_names, class_to_idx

def prepare_combined_training_data(class_to_idx, pv_sample_per_class=80):
    samples = []
    
    # 1. PlantDoc field train images
    plantdoc_train = PROJECT_ROOT / "data" / "plantdoc_extracted" / "train"
    field_count = 0
    if plantdoc_train.exists():
        for folder in plantdoc_train.iterdir():
            if not folder.is_dir():
                continue
            pv_target = PLANTDOC_TO_PV.get(folder.name)
            if not pv_target or pv_target not in class_to_idx:
                continue
            label = class_to_idx[pv_target]
            imgs = list(folder.glob("*.*"))
            for img_path in imgs:
                samples.append((img_path, label))
                field_count += 1

    print(f"[Data] Loaded {field_count} real-world field images from PlantDoc train.")

    # 2. Balanced PlantVillage train images
    pv_train_csv = PROJECT_ROOT / "training_results" / "dataset" / "train.csv"
    pv_count = 0
    if pv_train_csv.exists():
        import csv
        per_class = {}
        with open(pv_train_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cname = row["class_name"]
                if cname in class_to_idx:
                    per_class.setdefault(cname, []).append(PROJECT_ROOT / row["image_path"])

        random.seed(42)
        for cname, paths in per_class.items():
            selected = paths[:pv_sample_per_class] if len(paths) > pv_sample_per_class else paths
            label = class_to_idx[cname]
            for p in selected:
                if p.exists():
                    samples.append((p, label))
                    pv_count += 1

    print(f"[Data] Loaded {pv_count} laboratory reference images from PlantVillage.")
    print(f"[Data] Total combined fine-tuning samples: {len(samples)}")
    return samples

def evaluate_model(model, loader):
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for inputs, targets in loader:
            inputs = inputs.to(DEVICE)
            targets = targets.to(DEVICE)
            outputs = model(inputs)
            preds = outputs.argmax(dim=1)
            correct += (preds == targets).sum().item()
            total += targets.size(0)
    return correct / max(1, total)

def main():
    print("=" * 65)
    print("Fine-Tuning MobileNetV3 for Real-World Field Robustness")
    print("=" * 65)
    print(f"Device: {DEVICE}")

    class_names, class_to_idx = load_class_mapping()
    num_classes = len(class_names)

    # Prepare datasets
    train_samples = prepare_combined_training_data(class_to_idx, pv_sample_per_class=80)
    random.shuffle(train_samples)
    train_dataset = CombinedCropDataset(train_samples, transform=train_transforms)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=0)

    # Test dataset (independent PlantDoc test set)
    plantdoc_test = PROJECT_ROOT / "data" / "plantdoc_extracted" / "test"
    test_samples = []
    if plantdoc_test.exists():
        for folder in plantdoc_test.iterdir():
            if not folder.is_dir():
                continue
            pv_target = PLANTDOC_TO_PV.get(folder.name)
            if not pv_target or pv_target not in class_to_idx:
                continue
            label = class_to_idx[pv_target]
            for img_path in folder.glob("*.*"):
                test_samples.append((img_path, label))

    test_dataset = CombinedCropDataset(test_samples, transform=eval_transforms)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False, num_workers=0)
    print(f"[Data] Independent real-world test samples: {len(test_samples)}")

    # Load existing model
    model = mobilenet_v3_small(weights=None)
    model.classifier[3] = nn.Linear(model.classifier[3].in_features, num_classes)

    ckpt_path = PROJECT_ROOT / "backend" / "model" / "crop_disease_mobilenetv3.pth"
    if ckpt_path.exists():
        print(f"[Model] Loading existing checkpoint from {ckpt_path}")
        state = torch.load(ckpt_path, map_location=DEVICE)
        model.load_state_dict(state)
    else:
        print("[Model] Using default ImageNet weights...")
        model = mobilenet_v3_small(weights=MobileNet_V3_Small_Weights.DEFAULT)
        model.classifier[3] = nn.Linear(model.classifier[3].in_features, num_classes)

    model = model.to(DEVICE)

    # Initial test accuracy before fine-tuning
    pre_acc = evaluate_model(model, test_loader)
    print(f"\n[Baseline] Initial PlantDoc Field Test Accuracy: {pre_acc * 100:.2f}%")

    # Training settings
    criterion = nn.CrossEntropyLoss(label_smoothing=0.08)
    # Fine-tune classifier with 2e-4, backbone with 5e-5
    backbone_params = [p for n, p in model.named_parameters() if not n.startswith("classifier.3")]
    classifier_params = model.classifier[3].parameters()
    optimizer = AdamW([
        {"params": backbone_params, "lr": 5e-5},
        {"params": classifier_params, "lr": 2e-4}
    ], weight_decay=1e-4)

    epochs = 2
    best_acc = pre_acc

    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        t0 = time.time()

        for step, (inputs, targets) in enumerate(train_loader):
            inputs = inputs.to(DEVICE)
            targets = targets.to(DEVICE)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * targets.size(0)
            preds = outputs.argmax(dim=1)
            correct += (preds == targets).sum().item()
            total += targets.size(0)

            if (step + 1) % 35 == 0 or (step + 1) == len(train_loader):
                elapsed = time.time() - t0
                print(f"  Epoch [{epoch}/{epochs}] Step [{step+1}/{len(train_loader)}] Loss: {loss.item():.4f} Acc: {correct/total*100:.1f}% ({elapsed:.1f}s)", flush=True)

        epoch_acc = evaluate_model(model, test_loader)
        print(f"Epoch {epoch} Completed. PlantDoc Field Test Accuracy: {epoch_acc * 100:.2f}%\n", flush=True)

        # Save improved checkpoint
        if epoch_acc >= best_acc:
            best_acc = epoch_acc
            print(f"[*] Saving best model checkpoint (Field Test Acc: {best_acc*100:.2f}%) to {ckpt_path}")
            torch.save(model.state_dict(), ckpt_path)

    # Save final checkpoint
    print(f"\n[*] Saving final fine-tuned model checkpoint to {ckpt_path}")
    torch.save(model.state_dict(), ckpt_path)

    # Export to ONNX
    print("\n[*] Exporting fine-tuned model to ONNX...")
    model.eval()
    dummy_input = torch.randn(1, 3, 224, 224, device=DEVICE)

    onnx_destinations = [
        PROJECT_ROOT / "backend" / "model" / "artifacts" / "model.onnx",
        PROJECT_ROOT / "model" / "artifacts" / "model.onnx",
    ]

    for dest in onnx_destinations:
        dest.parent.mkdir(parents=True, exist_ok=True)
        torch.onnx.export(
            model,
            dummy_input,
            str(dest),
            input_names=["input"],
            output_names=["output"],
            dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}},
            opset_version=14,
        )
        print(f"  Exported ONNX model -> {dest} ({dest.stat().st_size:,} bytes)")

    print("\n[SUCCESS] Fine-tuning and ONNX export completed!")

if __name__ == "__main__":
    main()

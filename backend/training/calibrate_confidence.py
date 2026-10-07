import json
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision.models import (
    mobilenet_v3_small,
    MobileNet_V3_Small_Weights
)

from dataset import create_datasets


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = PROJECT_ROOT / "backend" / "model" / "crop_disease_mobilenetv3.pth"
CLASS_NAMES_PATH = PROJECT_ROOT / "backend" / "model" / "class_names.json"
OUTPUT_PATH = PROJECT_ROOT / "backend" / "model" / "confidence_temperature.json"

BATCH_SIZE = 64


def load_model(class_count, device):
    model = mobilenet_v3_small(
        weights=MobileNet_V3_Small_Weights.DEFAULT
    )

    input_features = model.classifier[3].in_features

    model.classifier[3] = nn.Linear(
        input_features,
        class_count
    )

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=device,
        weights_only=True
    )

    model.load_state_dict(checkpoint)
    model.to(device)
    model.eval()

    return model


def collect_validation_logits(model, validation_dataset, device):
    loader = DataLoader(
        validation_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0
    )

    all_logits = []
    all_labels = []

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)

            logits = model(images)

            all_logits.append(logits.cpu())
            all_labels.append(labels)

    return (
        torch.cat(all_logits),
        torch.cat(all_labels)
    )


def find_temperature(logits, labels, device):
    temperature = nn.Parameter(
        torch.ones(1, device=device) * 1.0
    )

    criterion = nn.CrossEntropyLoss()

    optimizer = torch.optim.LBFGS(
        [temperature],
        lr=0.01,
        max_iter=100
    )

    logits = logits.to(device)
    labels = labels.to(device)

    def closure():
        optimizer.zero_grad()

        loss = criterion(
            logits / temperature,
            labels
        )

        loss.backward()

        return loss

    optimizer.step(closure)

    value = temperature.item()

    # Temperature must be positive.
    value = max(value, 0.01)

    return value


def main():
    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print("Device:", device)
    print("Loading validation dataset...")

    _, validation_dataset, _, class_names = create_datasets()

    print("Validation samples:", len(validation_dataset))
    print("Number of classes:", len(class_names))

    model = load_model(
        len(class_names),
        device
    )

    print("Collecting validation logits...")

    logits, labels = collect_validation_logits(
        model,
        validation_dataset,
        device
    )

    print("Finding calibration temperature...")

    temperature = find_temperature(
        logits,
        labels,
        device
    )

    print()
    print("Calibration complete.")
    print("Temperature:", temperature)

    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            {
                "temperature": temperature,
                "method": "temperature_scaling",
                "validation_samples": len(validation_dataset),
                "number_of_classes": len(class_names)
            },
            file,
            indent=4
        )

    print()
    print("Saved:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
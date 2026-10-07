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

MODEL_PATH = (
    PROJECT_ROOT
    / "backend"
    / "model"
    / "crop_disease_mobilenetv3.pth"
)

TEMPERATURE_PATH = (
    PROJECT_ROOT
    / "backend"
    / "model"
    / "confidence_temperature.json"
)

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


def main():

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print("Device:", device)

    with open(
        TEMPERATURE_PATH,
        "r",
        encoding="utf-8"
    ) as file:
        temperature = json.load(file)["temperature"]

    print("Temperature:", temperature)

    _, validation_dataset, _, class_names = create_datasets()

    print("Validation samples:", len(validation_dataset))

    model = load_model(
        len(class_names),
        device
    )

    loader = DataLoader(
        validation_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0
    )

    correct_confidences = []
    incorrect_confidences = []

    with torch.no_grad():

        for images, labels in loader:

            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)

            probabilities = torch.softmax(
                outputs / temperature,
                dim=1
            )

            confidence, predictions = torch.max(
                probabilities,
                dim=1
            )

            correct = predictions == labels

            correct_confidences.extend(
                (confidence[correct] * 100)
                .cpu()
                .tolist()
            )

            incorrect_confidences.extend(
                (confidence[~correct] * 100)
                .cpu()
                .tolist()
            )

    def stats(values):

        if not values:
            return {
                "count": 0
            }

        values = sorted(values)

        n = len(values)

        def percentile(p):
            index = int((p / 100) * (n - 1))
            return values[index]

        return {
            "count": n,
            "minimum": values[0],
            "p10": percentile(10),
            "p25": percentile(25),
            "median": percentile(50),
            "p75": percentile(75),
            "p90": percentile(90),
            "p95": percentile(95),
            "p99": percentile(99),
            "maximum": values[-1]
        }

    print()
    print("CORRECT PREDICTIONS")
    print(stats(correct_confidences))

    print()
    print("INCORRECT PREDICTIONS")
    print(stats(incorrect_confidences))

    output = {
        "temperature": temperature,
        "correct_predictions": stats(correct_confidences),
        "incorrect_predictions": stats(incorrect_confidences)
    }

    output_path = (
        PROJECT_ROOT
        / "backend"
        / "model"
        / "confidence_analysis.json"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            output,
            file,
            indent=4
        )

    print()
    print("Saved:")
    print(output_path)


if __name__ == "__main__":
    main()
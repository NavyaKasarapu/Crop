import json
import sys
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score
)

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent)
)

from dataset import create_datasets
from train import create_model


# ============================================================
# Paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    PROJECT_ROOT
    / "backend"
    / "model"
    / "crop_disease_mobilenetv3.pth"
)

MODEL_DIR = (
    PROJECT_ROOT
    / "backend"
    / "model"
)

RESULTS_DIR = (
    PROJECT_ROOT
    / "training_results"
)


# ============================================================
# Configuration
# ============================================================

BATCH_SIZE = 32

NUM_WORKERS = 0

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 70)
    print("Crop Disease AI - MobileNetV3-Small Test Evaluation")
    print("=" * 70)

    print(
        f"\nDevice: {DEVICE}"
    )

    # --------------------------------------------------------
    # Load dataset
    # --------------------------------------------------------

    print("\nLoading test dataset...")

    (
        _,
        _,
        test_dataset,
        class_names
    ) = create_datasets()

    print(
        f"Test samples: {len(test_dataset)}"
    )

    print(
        f"Number of classes: {len(class_names)}"
    )

    # --------------------------------------------------------
    # Test loader
    # --------------------------------------------------------

    test_loader = DataLoader(
        test_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
        pin_memory=False
    )

    # --------------------------------------------------------
    # Load model
    # --------------------------------------------------------

    print("\nLoading MobileNetV3-Small...")

    model = create_model(
        class_names
    )

    print(
        f"Loading checkpoint:"
    )

    print(MODEL_PATH)

    state_dict = torch.load(
        MODEL_PATH,
        map_location=DEVICE,
        weights_only=True
    )

    model.load_state_dict(
        state_dict
    )

    model.eval()

    print(
        "Checkpoint loaded successfully."
    )

    # --------------------------------------------------------
    # Prediction
    # --------------------------------------------------------

    all_predictions = []

    all_labels = []

    print("\nRunning test evaluation...")

    with torch.no_grad():

        for batch_index, (images, labels) in enumerate(
            test_loader
        ):

            images = images.to(DEVICE)

            logits = model(
                images
            )

            predictions = (
                logits.argmax(
                    dim=1
                )
                .cpu()
                .tolist()
            )

            all_predictions.extend(
                predictions
            )

            all_labels.extend(
                labels.tolist()
            )

            if (batch_index + 1) % 50 == 0:

                print(
                    f"  Processed "
                    f"{(batch_index + 1) * BATCH_SIZE} "
                    f"/ {len(test_dataset)} images"
                )

    # --------------------------------------------------------
    # Accuracy
    # --------------------------------------------------------

    accuracy = accuracy_score(
        all_labels,
        all_predictions
    )

    # --------------------------------------------------------
    # Classification report
    # --------------------------------------------------------

    report = classification_report(
        all_labels,
        all_predictions,
        target_names=class_names,
        output_dict=True,
        zero_division=0
    )

    # --------------------------------------------------------
    # Confusion matrix
    # --------------------------------------------------------

    matrix = confusion_matrix(
        all_labels,
        all_predictions
    )

    # --------------------------------------------------------
    # Display overall results
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TEST RESULTS")
    print("=" * 70)

    print(
        f"\nTest Accuracy: "
        f"{accuracy * 100:.2f}%"
    )

    print(
        f"\nMacro Precision: "
        f"{report['macro avg']['precision'] * 100:.2f}%"
    )

    print(
        f"Macro Recall: "
        f"{report['macro avg']['recall'] * 100:.2f}%"
    )

    print(
        f"Macro F1-Score: "
        f"{report['macro avg']['f1-score'] * 100:.2f}%"
    )

    print(
        f"\nWeighted Precision: "
        f"{report['weighted avg']['precision'] * 100:.2f}%"
    )

    print(
        f"Weighted Recall: "
        f"{report['weighted avg']['recall'] * 100:.2f}%"
    )

    print(
        f"Weighted F1-Score: "
        f"{report['weighted avg']['f1-score'] * 100:.2f}%"
    )

    # --------------------------------------------------------
    # Per-class results
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("PER-CLASS RESULTS")
    print("=" * 70)

    for class_name in class_names:

        metrics = report[class_name]

        print(
            f"\n{class_name}"
        )

        print(
            f"  Precision: "
            f"{metrics['precision'] * 100:.2f}%"
        )

        print(
            f"  Recall: "
            f"{metrics['recall'] * 100:.2f}%"
        )

        print(
            f"  F1-score: "
            f"{metrics['f1-score'] * 100:.2f}%"
        )

        print(
            f"  Support: "
            f"{int(metrics['support'])}"
        )

    # --------------------------------------------------------
    # Save metrics
    # --------------------------------------------------------

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    metrics = {
        "model": "MobileNetV3-Small",
        "test_samples": len(test_dataset),
        "number_of_classes": len(class_names),
        "accuracy": accuracy,
        "macro_precision": report["macro avg"]["precision"],
        "macro_recall": report["macro avg"]["recall"],
        "macro_f1": report["macro avg"]["f1-score"],
        "weighted_precision":
            report["weighted avg"]["precision"],
        "weighted_recall":
            report["weighted avg"]["recall"],
        "weighted_f1":
            report["weighted avg"]["f1-score"],
        "classification_report": report,
        "confusion_matrix": matrix.tolist()
    }

    metrics_path = (
        MODEL_DIR
        / "metrics.json"
    )

    with metrics_path.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            metrics,
            file,
            indent=4
        )

    # --------------------------------------------------------
    # Save confusion matrix
    # --------------------------------------------------------

    confusion_matrix_path = (
        RESULTS_DIR
        / "confusion_matrix.json"
    )

    with confusion_matrix_path.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            matrix.tolist(),
            file,
            indent=4
        )

    # --------------------------------------------------------
    # Final
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("EVALUATION COMPLETED")
    print("=" * 70)

    print(
        f"\nMetrics saved to:"
    )

    print(metrics_path)

    print(
        f"\nConfusion matrix saved to:"
    )

    print(confusion_matrix_path)


if __name__ == "__main__":

    main()
import json
import time
from pathlib import Path

import torch
from torch import nn
from torch.optim import AdamW
from torch.utils.data import DataLoader
from torchvision.models import (
    mobilenet_v3_small,
    MobileNet_V3_Small_Weights
)

from dataset import create_datasets


# ============================================================
# Project paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_DIR = PROJECT_ROOT / "backend" / "model"
RESULTS_DIR = PROJECT_ROOT / "training_results"


# ============================================================
# Training configuration
# ============================================================

MODEL_NAME = "MobileNetV3-Small"

IMAGE_SIZE = 224

# CPU-friendly configuration
BATCH_SIZE = 32

EPOCHS = 5

LEARNING_RATE = 1e-3

WEIGHT_DECAY = 1e-4

PATIENCE = 2

NUM_WORKERS = 0

RANDOM_SEED = 42


# ============================================================
# Device
# ============================================================

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


# ============================================================
# Reproducibility
# ============================================================

def set_seed(seed):

    torch.manual_seed(seed)

    if torch.cuda.is_available():

        torch.cuda.manual_seed_all(seed)


# ============================================================
# Save JSON
# ============================================================

def save_json(data, path):

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with path.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4
        )


# ============================================================
# Create data loaders
# ============================================================

def create_data_loaders():

    (
        train_dataset,
        val_dataset,
        test_dataset,
        class_names
    ) = create_datasets()

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=NUM_WORKERS,
        pin_memory=False
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
        pin_memory=False
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
        pin_memory=False
    )

    return (
        train_loader,
        val_loader,
        test_loader,
        class_names
    )


# ============================================================
# Build MobileNetV3-Small
# ============================================================

def create_model(class_names):

    number_of_classes = len(class_names)

    print("\nLoading pretrained MobileNetV3-Small...")

    print(
        "ImageNet pretrained weights will be used."
    )

    model = mobilenet_v3_small(
        weights=MobileNet_V3_Small_Weights.DEFAULT
    )

    # --------------------------------------------------------
    # Replace the final classifier layer
    # --------------------------------------------------------

    input_features = model.classifier[3].in_features

    model.classifier[3] = nn.Linear(
        input_features,
        number_of_classes
    )

    print(
        f"Number of output classes: "
        f"{number_of_classes}"
    )

    return model.to(DEVICE)


# ============================================================
# Calculate accuracy
# ============================================================

def calculate_accuracy(
    predictions,
    labels
):

    predicted_labels = predictions.argmax(
        dim=1
    )

    correct = (
        predicted_labels == labels
    ).sum().item()

    total = labels.size(0)

    return correct, total


# ============================================================
# Training epoch
# ============================================================

def train_one_epoch(
    model,
    loader,
    optimizer,
    criterion
):

    model.train()

    total_loss = 0.0
    total_correct = 0
    total_samples = 0

    for step, (images, labels) in enumerate(loader):

        images = images.to(DEVICE)
        labels = labels.to(DEVICE)

        # ----------------------------------------------------
        # Forward pass
        # ----------------------------------------------------

        logits = model(images)

        # ----------------------------------------------------
        # Calculate loss
        # ----------------------------------------------------

        loss = criterion(
            logits,
            labels
        )

        # ----------------------------------------------------
        # Backpropagation
        # ----------------------------------------------------

        optimizer.zero_grad(
            set_to_none=True
        )

        loss.backward()

        optimizer.step()

        # ----------------------------------------------------
        # Metrics
        # ----------------------------------------------------

        total_loss += loss.item()

        correct, count = calculate_accuracy(
            logits,
            labels
        )

        total_correct += correct
        total_samples += count

        if (step + 1) % 100 == 0:

            print(
                f"  Batch {step + 1}/{len(loader)} "
                f"| Loss: {loss.item():.4f}"
            )

    average_loss = (
        total_loss / len(loader)
    )

    accuracy = (
        total_correct / total_samples
    )

    return average_loss, accuracy


# ============================================================
# Validation epoch
# ============================================================

def validate(
    model,
    loader,
    criterion
):

    model.eval()

    total_loss = 0.0
    total_correct = 0
    total_samples = 0

    with torch.no_grad():

        for images, labels in loader:

            images = images.to(DEVICE)
            labels = labels.to(DEVICE)

            logits = model(images)

            loss = criterion(
                logits,
                labels
            )

            total_loss += loss.item()

            correct, count = calculate_accuracy(
                logits,
                labels
            )

            total_correct += correct
            total_samples += count

    average_loss = (
        total_loss / len(loader)
    )

    accuracy = (
        total_correct / total_samples
    )

    return average_loss, accuracy


# ============================================================
# Save training history
# ============================================================

def save_training_history(history):

    history_path = (
        RESULTS_DIR
        / "training_history_mobilenetv3.json"
    )

    save_json(
        history,
        history_path
    )


# ============================================================
# Main training function
# ============================================================

def main():

    set_seed(RANDOM_SEED)

    print("=" * 70)
    print("Crop Disease AI - MobileNetV3-Small Training")
    print("=" * 70)

    print(
        f"\nDevice: {DEVICE}"
    )

    print(
        f"Model: {MODEL_NAME}"
    )

    print(
        f"Batch size: {BATCH_SIZE}"
    )

    print(
        f"Epochs: {EPOCHS}"
    )

    print(
        f"Learning rate: {LEARNING_RATE}"
    )

    # --------------------------------------------------------
    # Data
    # --------------------------------------------------------

    print("\nPreparing datasets...")

    (
        train_loader,
        val_loader,
        test_loader,
        class_names
    ) = create_data_loaders()

    print(
        f"Number of classes: "
        f"{len(class_names)}"
    )

    print(
        f"Training samples: "
        f"{len(train_loader.dataset)}"
    )

    print(
        f"Validation samples: "
        f"{len(val_loader.dataset)}"
    )

    print(
        f"Test samples: "
        f"{len(test_loader.dataset)}"
    )

    print("\nSupported classes:")

    for index, class_name in enumerate(class_names):

        print(
            f"  {index}: {class_name}"
        )

    # --------------------------------------------------------
    # Model
    # --------------------------------------------------------

    model = create_model(
        class_names
    )

    # --------------------------------------------------------
    # Loss
    # --------------------------------------------------------

    criterion = nn.CrossEntropyLoss()

    # --------------------------------------------------------
    # Optimizer
    # --------------------------------------------------------

    optimizer = AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY
    )

    # --------------------------------------------------------
    # Learning-rate scheduler
    # --------------------------------------------------------

    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="max",
        factor=0.5,
        patience=1,
        min_lr=1e-6
    )

    # --------------------------------------------------------
    # Training history
    # --------------------------------------------------------

    history = {
        "train_loss": [],
        "train_accuracy": [],
        "validation_loss": [],
        "validation_accuracy": [],
        "learning_rate": []
    }

    # --------------------------------------------------------
    # Best model tracking
    # --------------------------------------------------------

    best_val_accuracy = 0.0

    epochs_without_improvement = 0

    best_model_path = (
        MODEL_DIR
        / "crop_disease_mobilenetv3.pth"
    )

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Training loop
    # --------------------------------------------------------

    for epoch in range(1, EPOCHS + 1):

        print("\n" + "=" * 70)

        print(
            f"Epoch {epoch}/{EPOCHS}"
        )

        print("=" * 70)

        start_time = time.time()

        train_loss, train_accuracy = (
            train_one_epoch(
                model,
                train_loader,
                optimizer,
                criterion
            )
        )

        val_loss, val_accuracy = (
            validate(
                model,
                val_loader,
                criterion
            )
        )

        current_lr = (
            optimizer.param_groups[0]["lr"]
        )

        scheduler.step(
            val_accuracy
        )

        elapsed = (
            time.time() - start_time
        )

        # ----------------------------------------------------
        # Save history
        # ----------------------------------------------------

        history["train_loss"].append(
            train_loss
        )

        history["train_accuracy"].append(
            train_accuracy
        )

        history["validation_loss"].append(
            val_loss
        )

        history["validation_accuracy"].append(
            val_accuracy
        )

        history["learning_rate"].append(
            current_lr
        )

        save_training_history(
            history
        )

        # ----------------------------------------------------
        # Display metrics
        # ----------------------------------------------------

        print("\nEpoch results:")

        print(
            f"Training Loss: "
            f"{train_loss:.4f}"
        )

        print(
            f"Training Accuracy: "
            f"{train_accuracy * 100:.2f}%"
        )

        print(
            f"Validation Loss: "
            f"{val_loss:.4f}"
        )

        print(
            f"Validation Accuracy: "
            f"{val_accuracy * 100:.2f}%"
        )

        print(
            f"Learning Rate: "
            f"{current_lr:.8f}"
        )

        print(
            f"Time: "
            f"{elapsed / 60:.2f} minutes"
        )

        # ----------------------------------------------------
        # Save best model
        # ----------------------------------------------------

        if val_accuracy > best_val_accuracy:

            best_val_accuracy = val_accuracy

            epochs_without_improvement = 0

            torch.save(
                model.state_dict(),
                best_model_path
            )

            print(
                "\nBest MobileNetV3-Small checkpoint saved."
            )

            print(
                f"Best validation accuracy: "
                f"{best_val_accuracy * 100:.2f}%"
            )

        else:

            epochs_without_improvement += 1

            print(
                "\nNo validation improvement."
            )

            print(
                f"Early stopping counter: "
                f"{epochs_without_improvement}/{PATIENCE}"
            )

        # ----------------------------------------------------
        # Early stopping
        # ----------------------------------------------------

        if epochs_without_improvement >= PATIENCE:

            print(
                "\nEarly stopping triggered."
            )

            break

    # --------------------------------------------------------
    # Save class names
    # --------------------------------------------------------

    class_names_path = (
        MODEL_DIR
        / "class_names.json"
    )

    save_json(
        class_names,
        class_names_path
    )

    # --------------------------------------------------------
    # Save training configuration
    # --------------------------------------------------------

    config = {
        "model_name": MODEL_NAME,
        "image_size": IMAGE_SIZE,
        "batch_size": BATCH_SIZE,
        "epochs": EPOCHS,
        "learning_rate": LEARNING_RATE,
        "weight_decay": WEIGHT_DECAY,
        "patience": PATIENCE,
        "random_seed": RANDOM_SEED,
        "device": str(DEVICE),
        "number_of_classes": len(class_names),
        "number_of_training_samples":
            len(train_loader.dataset),
        "number_of_validation_samples":
            len(val_loader.dataset),
        "number_of_test_samples":
            len(test_loader.dataset)
    }

    config_path = (
        RESULTS_DIR
        / "training_config_mobilenetv3.json"
    )

    save_json(
        config,
        config_path
    )

    # --------------------------------------------------------
    # Final output
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TRAINING COMPLETED")
    print("=" * 70)

    print(
        f"\nBest validation accuracy: "
        f"{best_val_accuracy * 100:.2f}%"
    )

    print(
        "\nBest model:"
    )

    print(best_model_path)

    print(
        "\nClass names:"
    )

    print(class_names_path)

    print(
        "\nTraining history:"
    )

    print(
        RESULTS_DIR
        / "training_history_mobilenetv3.json"
    )

    print(
        "\nNext step will be test-set evaluation."
    )

    try:
        from export_onnx import export as export_to_onnx
        print("\nExporting model to ONNX...")
        export_to_onnx()
    except Exception as exc:
        print(f"Warning: ONNX export step encountered an issue: {exc}")


if __name__ == "__main__":

    main()
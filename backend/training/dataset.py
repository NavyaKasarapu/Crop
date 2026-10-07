from pathlib import Path
import csv

import torch
from torch.utils.data import Dataset
from PIL import Image
from torchvision import transforms


# ============================================================
# Project paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_ROOT = (
    PROJECT_ROOT
    / "PlantVillage-Dataset"
    / "raw"
    / "color"
)

SPLIT_ROOT = (
    PROJECT_ROOT
    / "training_results"
    / "dataset"
)


# ============================================================
# Image configuration
# ============================================================

IMAGE_SIZE = 224


# ImageNet normalization used by the pretrained ViT
IMAGE_MEAN = [
    0.485,
    0.456,
    0.406,
]

IMAGE_STD = [
    0.229,
    0.224,
    0.225,
]


# ============================================================
# Training transforms
# ============================================================

train_transform = transforms.Compose(
    [
        transforms.RandomResizedCrop(
            IMAGE_SIZE,
            scale=(0.8, 1.0)
        ),

        transforms.RandomHorizontalFlip(
            p=0.5
        ),

        transforms.RandomRotation(
            degrees=10
        ),

        transforms.ColorJitter(
            brightness=0.15,
            contrast=0.15
        ),

        transforms.ToTensor(),

        transforms.Normalize(
            mean=IMAGE_MEAN,
            std=IMAGE_STD
        ),
    ]
)


# ============================================================
# Validation / Test transforms
# ============================================================

eval_transform = transforms.Compose(
    [
        transforms.Resize(
            (IMAGE_SIZE, IMAGE_SIZE)
        ),

        transforms.ToTensor(),

        transforms.Normalize(
            mean=IMAGE_MEAN,
            std=IMAGE_STD
        ),
    ]
)


# ============================================================
# Dataset class
# ============================================================

class PlantVillageDataset(Dataset):

    def __init__(
        self,
        csv_file,
        class_to_index,
        transform=None
    ):

        self.csv_file = Path(csv_file)

        self.class_to_index = class_to_index

        self.transform = transform

        self.samples = []

        self._load_csv()

    # --------------------------------------------------------
    # Load CSV
    # --------------------------------------------------------

    def _load_csv(self):

        if not self.csv_file.exists():

            raise FileNotFoundError(
                f"CSV file not found:\n{self.csv_file}"
            )

        with self.csv_file.open(
            "r",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                image_path = (
                    PROJECT_ROOT / row["image_path"]
                )

                class_name = row["class_name"]

                if class_name not in self.class_to_index:

                    raise ValueError(
                        f"Unknown class: {class_name}"
                    )

                label = self.class_to_index[
                    class_name
                ]

                self.samples.append(
                    (
                        image_path,
                        label
                    )
                )

    # --------------------------------------------------------
    # Number of samples
    # --------------------------------------------------------

    def __len__(self):

        return len(self.samples)

    # --------------------------------------------------------
    # Get one sample
    # --------------------------------------------------------

    def __getitem__(self, index):

        image_path, label = self.samples[index]

        try:

            image = Image.open(
                image_path
            ).convert("RGB")

        except Exception as error:

            raise RuntimeError(
                f"Unable to read image:\n"
                f"{image_path}\n"
                f"Error: {error}"
            )

        if self.transform is not None:

            image = self.transform(image)

        return image, label


# ============================================================
# Class discovery
# ============================================================

def load_class_names():

    class_names_file = (
        SPLIT_ROOT / "class_names.txt"
    )

    if not class_names_file.exists():

        raise FileNotFoundError(
            f"Class names file not found:\n"
            f"{class_names_file}"
        )

    class_names = [
        line.strip()
        for line in class_names_file.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    if not class_names:

        raise RuntimeError(
            "No class names were found."
        )

    return class_names


def create_class_mapping():

    class_names = load_class_names()

    class_to_index = {
        class_name: index
        for index, class_name
        in enumerate(class_names)
    }

    return class_names, class_to_index


# ============================================================
# Create datasets
# ============================================================

def create_datasets():

    class_names, class_to_index = (
        create_class_mapping()
    )

    train_csv = SPLIT_ROOT / "train.csv"
    val_csv = SPLIT_ROOT / "val.csv"
    test_csv = SPLIT_ROOT / "test.csv"

    train_dataset = PlantVillageDataset(
        csv_file=train_csv,
        class_to_index=class_to_index,
        transform=train_transform
    )

    val_dataset = PlantVillageDataset(
        csv_file=val_csv,
        class_to_index=class_to_index,
        transform=eval_transform
    )

    test_dataset = PlantVillageDataset(
        csv_file=test_csv,
        class_to_index=class_to_index,
        transform=eval_transform
    )

    return (
        train_dataset,
        val_dataset,
        test_dataset,
        class_names
    )


# ============================================================
# Simple verification
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("PlantVillage ViT Dataset Loader Test")
    print("=" * 70)

    (
        train_dataset,
        val_dataset,
        test_dataset,
        class_names
    ) = create_datasets()

    print(
        f"\nNumber of classes: {len(class_names)}"
    )

    print(
        f"Training samples: {len(train_dataset)}"
    )

    print(
        f"Validation samples: {len(val_dataset)}"
    )

    print(
        f"Test samples: {len(test_dataset)}"
    )

    print(
        f"\nFirst 5 classes:"
    )

    for class_name in class_names[:5]:

        print(
            f"  {class_name}"
        )

    print("\nLoading one training image...")

    image, label = train_dataset[0]

    print(
        f"Image tensor shape: {tuple(image.shape)}"
    )

    print(
        f"Image tensor dtype: {image.dtype}"
    )

    print(
        f"Label index: {label}"
    )

    print(
        f"Label class: {class_names[label]}"
    )

    print("\nDataset loader test completed successfully.")
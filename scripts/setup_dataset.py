from pathlib import Path
from collections import Counter
import csv
import random

from PIL import Image


# ============================================================
# Configuration
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_PATH = PROJECT_ROOT / "PlantVillage-Dataset" / "raw" / "color"
OUTPUT_DIR = PROJECT_ROOT / "training_results" / "dataset"

RANDOM_SEED = 42

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}


# ============================================================
# Utility functions
# ============================================================

def is_valid_image(image_path: Path) -> bool:
    """
    Verify that an image can actually be opened and decoded.
    """
    try:
        with Image.open(image_path) as image:
            image.verify()

        return True

    except Exception:
        return False


def discover_images():
    """
    Discover images from:

    PlantVillage-Dataset/
        raw/
            color/
                Class_1/
                Class_2/
                ...
    """

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset directory was not found:\n{DATASET_PATH}"
        )

    class_directories = sorted(
        [
            directory
            for directory in DATASET_PATH.iterdir()
            if directory.is_dir()
        ]
    )

    if not class_directories:
        raise RuntimeError(
            "No class directories were found in the dataset."
        )

    records = []
    corrupted_images = []

    for class_directory in class_directories:

        class_name = class_directory.name

        image_files = sorted(
            [
                file
                for file in class_directory.rglob("*")
                if file.is_file()
                and file.suffix.lower() in SUPPORTED_EXTENSIONS
            ]
        )

        for image_path in image_files:

            if is_valid_image(image_path):

                records.append(
                    {
                        "image_path": str(
                            image_path.relative_to(PROJECT_ROOT)
                        ),
                        "class_name": class_name,
                    }
                )

            else:

                corrupted_images.append(
                    str(image_path.relative_to(PROJECT_ROOT))
                )

    return class_directories, records, corrupted_images


def stratified_split(records):
    """
    Perform a reproducible stratified split.

    Each class is split independently so that train,
    validation and test sets contain samples from every class.
    """

    random.seed(RANDOM_SEED)

    records_by_class = {}

    for record in records:

        class_name = record["class_name"]

        records_by_class.setdefault(
            class_name,
            []
        ).append(record)

    train_records = []
    val_records = []
    test_records = []

    for class_name, class_records in records_by_class.items():

        random.shuffle(class_records)

        total = len(class_records)

        train_end = int(total * TRAIN_RATIO)

        val_end = train_end + int(total * VAL_RATIO)

        train_records.extend(
            class_records[:train_end]
        )

        val_records.extend(
            class_records[train_end:val_end]
        )

        test_records.extend(
            class_records[val_end:]
        )

    random.shuffle(train_records)
    random.shuffle(val_records)
    random.shuffle(test_records)

    return train_records, val_records, test_records


def save_csv(records, filename):

    output_path = OUTPUT_DIR / filename

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "image_path",
                "class_name",
            ]
        )

        writer.writeheader()
        writer.writerows(records)

    return output_path


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 70)
    print("PlantVillage Dataset Setup")
    print("=" * 70)

    print(f"\nDataset path:")
    print(DATASET_PATH)

    print("\nChecking dataset...")

    class_directories, records, corrupted_images = (
        discover_images()
    )

    class_names = sorted(
        directory.name
        for directory in class_directories
    )

    print("\nDataset discovered successfully.")

    print(f"Number of classes : {len(class_names)}")
    print(f"Valid images      : {len(records)}")
    print(f"Corrupted images  : {len(corrupted_images)}")

    # --------------------------------------------------------
    # Class distribution
    # --------------------------------------------------------

    class_counts = Counter(
        record["class_name"]
        for record in records
    )

    print("\nImages per class:")
    print("-" * 70)

    for class_name in class_names:

        print(
            f"{class_name:<55} "
            f"{class_counts[class_name]}"
        )

    # --------------------------------------------------------
    # Split dataset
    # --------------------------------------------------------

    print("\nCreating train/validation/test split...")

    train_records, val_records, test_records = (
        stratified_split(records)
    )

    print("\nSplit completed.")

    print(f"Training images   : {len(train_records)}")
    print(f"Validation images : {len(val_records)}")
    print(f"Test images       : {len(test_records)}")

    # --------------------------------------------------------
    # Output directory
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Save CSV files
    # --------------------------------------------------------

    train_csv = save_csv(
        train_records,
        "train.csv"
    )

    val_csv = save_csv(
        val_records,
        "val.csv"
    )

    test_csv = save_csv(
        test_records,
        "test.csv"
    )

    # --------------------------------------------------------
    # Save class names
    # --------------------------------------------------------

    class_names_file = OUTPUT_DIR / "class_names.txt"

    class_names_file.write_text(
        "\n".join(class_names),
        encoding="utf-8"
    )

    # --------------------------------------------------------
    # Save corrupted image list
    # --------------------------------------------------------

    corrupted_file = OUTPUT_DIR / "corrupted_images.txt"

    corrupted_file.write_text(
        "\n".join(corrupted_images),
        encoding="utf-8"
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    summary_file = OUTPUT_DIR / "dataset_summary.txt"

    summary_lines = [
        "PlantVillage Dataset Summary",
        "=" * 50,
        f"Dataset path: {DATASET_PATH}",
        f"Number of classes: {len(class_names)}",
        f"Valid images: {len(records)}",
        f"Corrupted images: {len(corrupted_images)}",
        "",
        "Split:",
        f"Train: {len(train_records)}",
        f"Validation: {len(val_records)}",
        f"Test: {len(test_records)}",
        "",
        "Class distribution:",
    ]

    for class_name in class_names:

        summary_lines.append(
            f"{class_name}: {class_counts[class_name]}"
        )

    summary_file.write_text(
        "\n".join(summary_lines),
        encoding="utf-8"
    )

    # --------------------------------------------------------
    # Final output
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("DATASET SETUP COMPLETED")
    print("=" * 70)

    print("\nGenerated files:")

    print(train_csv)
    print(val_csv)
    print(test_csv)
    print(class_names_file)
    print(corrupted_file)
    print(summary_file)

    print("\nDataset is ready for the Vision Transformer training pipeline.")


if __name__ == "__main__":
    main()
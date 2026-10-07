"""
Export trained PyTorch MobileNetV3-Small crop disease classifier to ONNX.
Creates model/artifacts/model.onnx and model/artifacts/labels.json.
"""

import sys
from pathlib import Path
import json
import numpy as np

# Force UTF-8 encoding for Windows stdout/stderr
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import torch
import torch.nn as nn
from torchvision.models import mobilenet_v3_small
import onnx
import onnxruntime as ort

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_PTH_PATH = PROJECT_ROOT / "backend" / "model" / "crop_disease_mobilenetv3.pth"
CLASS_NAMES_PATH = PROJECT_ROOT / "backend" / "model" / "class_names.json"

TARGET_DIRS = [
    PROJECT_ROOT / "model" / "artifacts",
    PROJECT_ROOT / "backend" / "model" / "artifacts",
]


def export():
    print(f"Loading class names from {CLASS_NAMES_PATH}...")
    if not CLASS_NAMES_PATH.exists():
        raise FileNotFoundError(f"Class names file not found: {CLASS_NAMES_PATH}")

    with open(CLASS_NAMES_PATH, "r", encoding="utf-8") as f:
        class_names = json.load(f)

    num_classes = len(class_names)
    print(f"Number of classes: {num_classes}")

    print(f"Loading PyTorch model weights from {MODEL_PTH_PATH}...")
    if not MODEL_PTH_PATH.exists():
        raise FileNotFoundError(f"PyTorch model weights not found: {MODEL_PTH_PATH}")

    model = mobilenet_v3_small(weights=None)
    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, num_classes)

    checkpoint = torch.load(MODEL_PTH_PATH, map_location="cpu", weights_only=True)
    model.load_state_dict(checkpoint)
    model.eval()

    dummy_input = torch.randn(1, 3, 224, 224, dtype=torch.float32)

    with torch.no_grad():
        torch_out = model(dummy_input).numpy()

    for target_dir in TARGET_DIRS:
        target_dir.mkdir(parents=True, exist_ok=True)

        onnx_path = target_dir / "model.onnx"
        labels_path = target_dir / "labels.json"

        print(f"\nExporting ONNX model to {onnx_path}...")
        torch.onnx.export(
            model,
            dummy_input,
            str(onnx_path),
            export_params=True,
            opset_version=14,
            do_constant_folding=True,
            input_names=["input"],
            output_names=["output"],
            dynamic_axes={
                "input": {0: "batch_size"},
                "output": {0: "batch_size"},
            },
            dynamo=False,
        )

        print(f"Writing labels to {labels_path}...")
        with open(labels_path, "w", encoding="utf-8") as f:
            json.dump(class_names, f, indent=2)

        # Validate with onnx
        print("Checking ONNX model integrity...")
        onnx_model = onnx.load(str(onnx_path))
        onnx.checker.check_model(onnx_model)

        # Test inference with ONNX Runtime
        print("Testing ONNX Runtime session...")
        ort_session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
        ort_inputs = {"input": dummy_input.numpy()}
        ort_outs = ort_session.run(None, ort_inputs)

        # Verify output match
        diff = np.max(np.abs(torch_out - ort_outs[0]))
        print(f"Maximum absolute difference between PyTorch and ONNX: {diff:.6e}")
        assert diff < 1e-4, f"ONNX output differs significantly: {diff}"

    print("\n[SUCCESS] ONNX export and verification completed successfully!")


if __name__ == "__main__":
    export()

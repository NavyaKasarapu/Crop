import os
import sys
sys.path.insert(0, os.path.abspath("."))
from PIL import Image
import numpy as np
from backend.app.services.model_service import model_service

def test_pipeline():
    rice_dir = "data/test_rice"
    rice_files = [f for f in os.listdir(rice_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    print(f"Testing {len(rice_files)} Rice images...")
    
    # We will test our updated logic on rice
    for rf in rice_files:
        p = os.path.join(rice_dir, rf)
        im = Image.open(p).convert("RGB")
        # Let's inspect
        print(f"Rice: {rf}")

if __name__ == "__main__":
    test_pipeline()

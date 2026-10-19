import subprocess
import os
import re
import hashlib
from pathlib import Path

def sanitize_name(name):
    # Replace invalid Windows chars
    clean = re.sub(r'[<>:"/\\|?*]', '_', name)
    if len(clean) > 80:
        stem, ext = os.path.splitext(clean)
        h = hashlib.md5(clean.encode("utf-8")).hexdigest()[:8]
        clean = stem[:60] + "_" + h + ext
    return clean

def extract_set(subset_name):
    output_base = Path("data/plantdoc_extracted") / subset_name
    output_base.mkdir(parents=True, exist_ok=True)

    proc = subprocess.Popen(
        ["git", "ls-tree", "-r", "HEAD", subset_name],
        cwd="plantdoc_data",
        stdout=subprocess.PIPE
    )
    out, _ = proc.communicate()
    lines = [l.strip() for l in out.decode("utf-8", errors="ignore").split("\n") if l.strip()]

    count = 0
    errors = 0
    for line in lines:
        parts = line.split(None, 3)
        if len(parts) < 4:
            continue
        mode, obj_type, blob_hash, raw_path = parts
        rel_path_parts = raw_path.split("/")
        if len(rel_path_parts) > 1:
            rel_path_parts = rel_path_parts[1:]
        sanitized_parts = [sanitize_name(p) for p in rel_path_parts]
        dest_file = output_base / Path(*sanitized_parts)
        dest_file.parent.mkdir(parents=True, exist_ok=True)

        if dest_file.exists() and dest_file.stat().st_size > 0:
            count += 1
            continue

        try:
            blob_proc = subprocess.Popen(
                ["git", "cat-file", "-p", blob_hash],
                cwd="plantdoc_data",
                stdout=subprocess.PIPE
            )
            data, _ = blob_proc.communicate()
            dest_file.write_bytes(data)
            count += 1
        except Exception as e:
            errors += 1
            print(f"Error extracting {raw_path}: {e}")

    print(f"Successfully extracted {count} {subset_name} images (errors: {errors}) to {output_base}")

if __name__ == "__main__":
    print("Extracting PlantDoc test set...")
    extract_set("test")
    print("Extracting PlantDoc train set...")
    extract_set("train")
    print("Done!")

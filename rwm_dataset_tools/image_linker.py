import os
import shutil
from dataset_extractor import create_label_file

def link_image(src_path, dest_dir, image_id):
    ext = os.path.splitext(src_path)[1]
    dest_path = os.path.join(dest_dir, f"{image_id}{ext}")
    if not os.path.exists(dest_path):
        os.symlink(src_path, dest_path)
    return dest_path

def write_label_file(label_lines, dest_dir, image_id):
    label_path = os.path.join(dest_dir, f"{image_id}.txt")
    with open(label_path, "w") as f:
        for line in label_lines:
            f.write(line+"\n")
    return label_path

import os
import numpy as np
from config.dataset_config import RWM_IMAGES_PATH, EPPO_CODES

def center_enclosed(inner_box: np.ndarray, outer_box: np.ndarray) -> bool:
    center_x = (inner_box[0] + inner_box[2]) / 2.0
    center_y = (inner_box[1] + inner_box[3]) / 2.0
    return (outer_box[0] <= center_x <= outer_box[2]) and (outer_box[1] <= center_y <= outer_box[3])

def mkdir_p(path: str):
    os.makedirs(path, exist_ok=True)

def suffix(path: str) -> str:
    return path + "_old"

class AnnotationImageCache:
    def __init__(self):
        self.base_path = RWM_IMAGES_PATH

    def get_path(self, upload_id, filename):
        return os.path.join(self.base_path, filename)

def find_relevant_eppo(eppo_code: str, cotyledon_id: int) -> str:
    for code in EPPO_CODES:
        if eppo_code.startswith(code):
            eppo_code = code
    if eppo_code in EPPO_CODES:
        return eppo_code
    elif cotyledon_id == -100:
        return 'PPPMM'
    elif cotyledon_id == -101:
        return 'PPPDD'
    else:
        return None

def row_to_yolo(row: dict) -> str:
    eppo_code = row['EPPOCode']
    cotyledon_id = row['cotyledon']
    min_x = row['MinX']
    min_y = row['MinY']
    max_x = row['MaxX']
    max_y = row['MaxY']
    image_width = row['Width']
    image_height = row['Height']
    if eppo_code is None:
        return None
    eppo_code = find_relevant_eppo(eppo_code, cotyledon_id)
    if eppo_code is None:
        return None
    class_index = EPPO_CODES.index(eppo_code)
    box_width = max_x - min_x
    box_height = max_y - min_y
    center_x = min_x + box_width / 2.0
    center_y = min_y + box_height / 2.0
    center_x_norm = center_x / image_width
    center_y_norm = center_y / image_height
    box_width_norm = box_width / image_width
    box_height_norm = box_height / image_height
    return f"{class_index} {center_x_norm} {center_y_norm} {box_width_norm} {box_height_norm}"

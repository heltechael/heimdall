import numpy as np
from typing import Dict, Any, Optional, List

from config.dataset_config import EPPO_CODES

def center_enclosed(inner_box: np.ndarray, outer_box: np.ndarray) -> bool:
    inner_center_x = (inner_box[0] + inner_box[2]) / 2
    inner_center_y = (inner_box[1] + inner_box[3]) / 2
    
    return (
        outer_box[0] <= inner_center_x <= outer_box[2] and
        outer_box[1] <= inner_center_y <= outer_box[3]
    )

def find_relevant_eppo(eppo_code: str, cotyledon_id: int) -> Optional[str]:
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

def process_psez_annotations(annotations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    result = []
    psez_skip_count = 0
    
    annotations_by_image = {}
    for ann in annotations:
        image_id = ann['ImageId']
        if image_id not in annotations_by_image:
            annotations_by_image[image_id] = []
        annotations_by_image[image_id].append(ann)
    
    for ann in annotations:
        if ann['EPPOCode'] == 'PSEZ':
            psez_image_id = ann['ImageId']
            match_found = False
            
            for other_ann in annotations_by_image.get(psez_image_id, []):
                if other_ann['EPPOCode'] in ('ZEAMX', 'BEAVA', 'BRSOL'):
                    psez_box = np.array([ann['MinX'], ann['MinY'], ann['MaxX'], ann['MaxY']])
                    crop_box = np.array([other_ann['MinX'], other_ann['MinY'], other_ann['MaxX'], other_ann['MaxY']])
                    
                    if center_enclosed(psez_box, crop_box):
                        result.append(ann)
                        match_found = True
                        break
            
            if not match_found:
                psez_skip_count += 1
        else:
            result.append(ann)
    
    print(f"PSEZ annotations skipped: {psez_skip_count}")
    return result

def convert_to_yolo_format(
    ann: Dict[str, Any],
    eppo_codes: List[str]
) -> Optional[str]:
    eppo_code = ann['EPPOCode']
    cotyledon_id = ann['cotyledon']
    
    eppo_code = find_relevant_eppo(eppo_code, cotyledon_id)
    if eppo_code is None:
        return None
    
    try:
        class_index = eppo_codes.index(eppo_code)
    except ValueError:
        return None
    
    min_x, min_y = ann['MinX'], ann['MinY']
    max_x, max_y = ann['MaxX'], ann['MaxY']
    img_width, img_height = ann['Width'], ann['Height']
    
    box_width = max_x - min_x
    box_height = max_y - min_y
    center_x = min_x + (box_width / 2)
    center_y = min_y + (box_height / 2)
    
    center_x_norm = center_x / img_width
    center_y_norm = center_y / img_height
    width_norm = box_width / img_width
    height_norm = box_height / img_height
    
    return f"{class_index} {center_x_norm:.6f} {center_y_norm:.6f} {width_norm:.6f} {height_norm:.6f}"

import os
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

def center_enclosed(inner_box: np.ndarray, outer_box: np.ndarray) -> bool:
    inner_center_x = (inner_box[0] + inner_box[2]) / 2
    inner_center_y = (inner_box[1] + inner_box[3]) / 2
    
    return (outer_box[0] <= inner_center_x <= outer_box[2] and 
            outer_box[1] <= inner_center_y <= outer_box[3])

def find_relevant_eppo(eppo_code: str, cotyledon_id: int, eppo_codes: List[str]) -> Optional[str]:
    for valid_eppo in eppo_codes:
        if eppo_code.startswith(valid_eppo):
            eppo_code = valid_eppo
            
    if eppo_code in eppo_codes:
        return eppo_code
    elif cotyledon_id == -100:
        return 'PPPMM'
    elif cotyledon_id == -101:
        return 'PPPDD'
    else:
        return None

def convert_to_yolo_format(
        annotation: Dict[str, Any], 
        eppo_codes: List[str]
    ) -> Optional[str]:
    
    eppo_code = annotation['EPPOCode']
    cotyledon_id = annotation['cotyledon']
    min_x = annotation['MinX']
    min_y = annotation['MinY']
    max_x = annotation['MaxX']
    max_y = annotation['MaxY']
    image_width = annotation['Width']
    image_height = annotation['Height']
    
    eppo_code = find_relevant_eppo(eppo_code, cotyledon_id, eppo_codes)
    if eppo_code is None:
        return None
    
    class_index = eppo_codes.index(eppo_code)
    box_width = max_x - min_x
    box_height = max_y - min_y
    center_x = min_x + (box_width / 2)
    center_y = min_y + (box_height / 2)
    
    # Normalize coordinates to 0-1 range
    center_x_norm = center_x / float(image_width)
    center_y_norm = center_y / float(image_height)
    box_width_norm = box_width / float(image_width)
    box_height_norm = box_height / float(image_height)
    
    return f"{class_index} {center_x_norm} {center_y_norm} {box_width_norm} {box_height_norm}"

def filter_psez_annotations(annotations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    result = []
    skip_count = 0
    
    psez_annotations = {}
    for annotation in annotations:
        if annotation['EPPOCode'] == 'PSEZ':
            image_id = annotation['ImageId']
            if image_id not in psez_annotations:
                psez_annotations[image_id] = []
            psez_annotations[image_id].append(annotation)
        else:
            result.append(annotation)
    
    # Process PSEZ annotations
    for image_id, psez_items in psez_annotations.items():
        for psez in psez_items:
            psez_box = np.array([psez['MinX'], psez['MinY'], psez['MaxX'], psez['MaxY']])
            
            match_found = False
            for annotation in annotations:
                if (annotation['ImageId'] == image_id and 
                    annotation['EPPOCode'] in ('ZEAMX', 'BEAVA', 'BRSOL')):
                    
                    crop_box = np.array([
                        annotation['MinX'], 
                        annotation['MinY'], 
                        annotation['MaxX'], 
                        annotation['MaxY']
                    ])
                    
                    if center_enclosed(psez_box, crop_box):
                        result.append(psez)
                        match_found = True
                        break
            
            if not match_found:
                skip_count += 1
    
    print(f"Total PSEZ annotations skipped: {skip_count}")
    return result
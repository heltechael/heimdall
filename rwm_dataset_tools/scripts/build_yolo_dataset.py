import os
import sys
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.dataset_config import (
    EPPO_CODES, 
    IMAGE_IDS_HELD_BACK, 
    FIXED_UPLOAD_IDS_TRAIN, 
    FIXED_UPLOAD_IDS_VAL, 
    FIXED_UPLOAD_IDS_TEST,
    FIXED_IMAGE_IDS_TRAIN, 
    FIXED_IMAGE_IDS_VAL, 
    FIXED_IMAGE_IDS_TEST,
    BUCKET_PROB,
    RWM_IMAGES_PATH
)
from data_processing.db_connector import RWMDatabase
from data_processing.annotation_utils import filter_psez_annotations, convert_to_yolo_format
from data_processing.dataset_builder import YOLODatasetBuilder

def parse_args():
    parser = argparse.ArgumentParser(description='Build a YOLO dataset from RWM annotations')
    parser.add_argument('--output', type=str, default='./datasets/rwm_yolov11', help='Output directory for the dataset')
    parser.add_argument('--images-path', type=str, default=RWM_IMAGES_PATH, help='Path to the RWM images')
    return parser.parse_args()

def group_annotations_by_image(annotations: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    result = defaultdict(list)
    for annotation in annotations:
        result[annotation['ImageId']].append(annotation)
    return result

def main():
    args = parse_args()
    
    # Initialize the database connection and fetch data
    print("Connecting to RWM database...")
    db = RWMDatabase()
    annotations = db.get_labeled_data_for_training()
    print(f"Retrieved {len(annotations)} annotations from database")
    
    # Filter out held back images
    print(f"Filtering out {len(IMAGE_IDS_HELD_BACK)} held back images...")
    annotations = [a for a in annotations if a['ImageId'] not in IMAGE_IDS_HELD_BACK]
    print(f"Remaining annotations: {len(annotations)}")
    
    # Filter and process PSEZ annotations
    print("Processing PSEZ annotations...")
    annotations = filter_psez_annotations(annotations)
    
    # Group annotations by image
    annotations_by_image = group_annotations_by_image(annotations)
    print(f"Total number of images: {len(annotations_by_image)}")
    
    # Initialize dataset builder
    dataset_builder = YOLODatasetBuilder(
        dataset_root=args.output,
        images_source_path=args.images_path,
        eppo_codes=EPPO_CODES,
        image_ids_held_back=IMAGE_IDS_HELD_BACK,
        fixed_upload_ids_train=FIXED_UPLOAD_IDS_TRAIN,
        fixed_upload_ids_val=FIXED_UPLOAD_IDS_VAL,
        fixed_upload_ids_test=FIXED_UPLOAD_IDS_TEST,
        fixed_image_ids_train=FIXED_IMAGE_IDS_TRAIN,
        fixed_image_ids_val=FIXED_IMAGE_IDS_VAL,
        fixed_image_ids_test=FIXED_IMAGE_IDS_TEST,
        bucket_prob=BUCKET_PROB
    )
    
    # Setup directory structure
    print(f"Creating dataset structure in {args.output}...")
    dataset_builder.setup_directories()
    
    # Create dataset YAML file
    yaml_path = dataset_builder.create_dataset_yaml()
    print(f"Created dataset YAML at {yaml_path}")
    
    # Process annotations and create the dataset
    print("Processing annotations and creating dataset...")
    dataset_builder.process_annotations(annotations_by_image, sys.modules[__name__])
    
    print("Dataset creation complete!")

if __name__ == '__main__':
    main()
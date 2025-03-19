#!/usr/bin/env python3
import os
import argparse
import sys
from datetime import datetime

from data_processing.db_connector import RWMDatabaseConnector
from data_processing.dataset_builder import YOLODatasetBuilder

def parse_args():
    parser = argparse.ArgumentParser(description='Build a YOLO dataset from RoboWeedMaPS database')
    
    parser.add_argument('--output', '-o', type=str, required=True,
                      help='Output directory for the YOLO dataset')
    parser.add_argument('--db', type=str, default='RoboWeedMaps',
                      help='Database name (default: RoboWeedMaps)')
    parser.add_argument('--host', type=str, default='localhost',
                      help='Database host (default: localhost)')
    parser.add_argument('--user', type=str, default='SA',
                      help='Database user (default: SA)')
    parser.add_argument('--password', type=str, default='Robotbil123!',
                      help='Database password')
    parser.add_argument('--rwm-images', type=str, default='/data/roboweedmaps/images/',
                      help='Path to RWM images directory')
    parser.add_argument('--approved-only', action='store_true',
                      help='Use only APPROVED=1 annotations')
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    os.makedirs(args.output, exist_ok=True)
    
    print(f"Connecting to RWM database ({args.db})...")
    db = RWMDatabaseConnector(
        db_name=args.db,
        host=args.host,
        user=args.user,
        password=args.password
    )
    
    try:
        annotations = db.get_training_annotations()
        print(f"Retrieved {len(annotations)} annotations")
        
        if args.approved_only:
            annotations = [ann for ann in annotations if ann['APPROVED'] == 1]
            print(f"Filtered to {len(annotations)} approved annotations")
        
        builder = YOLODatasetBuilder(
            output_dir=args.output,
            rwm_images_path=args.rwm_images
        )
        
        print(f"Building YOLOv11 dataset in {args.output}...")
        stats = builder.build_from_annotations(annotations)
        
        print("\nDataset creation completed successfully!")
        print(f"Total images: {stats['train'] + stats['val'] + stats['test']}")
        print(f"Training images: {stats['train']}")
        print(f"Validation images: {stats['val']}")
        print(f"Test images: {stats['test']}")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()

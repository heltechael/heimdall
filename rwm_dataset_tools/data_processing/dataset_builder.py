import os
import shutil
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
import yaml

from config.dataset_config import (
    EPPO_CODES, IMAGE_IDS_HELD_BACK,
    FIXED_UPLOAD_IDS_TRAIN, FIXED_UPLOAD_IDS_VAL, FIXED_UPLOAD_IDS_TEST,
    FIXED_IMAGE_IDS_TRAIN, FIXED_IMAGE_IDS_VAL, FIXED_IMAGE_IDS_TEST,
    BUCKET_PROB, RWM_IMAGES_PATH
)
from data_processing.annotation_utils import process_psez_annotations, convert_to_yolo_format

class YOLODatasetBuilder:
    def __init__(
        self,
        output_dir: str,
        eppo_codes: List[str] = None,
        bucket_prob: List[float] = None,
        rwm_images_path: str = None
    ):
        self.output_dir = os.path.abspath(output_dir)
        self.eppo_codes = eppo_codes or EPPO_CODES
        self.bucket_prob = bucket_prob or BUCKET_PROB
        self.rwm_images_path = rwm_images_path or RWM_IMAGES_PATH
        
        self.images_dir = os.path.join(self.output_dir, 'images')
        self.labels_dir = os.path.join(self.output_dir, 'labels')
        
        self.train_images_dir = os.path.join(self.images_dir, 'train')
        self.val_images_dir = os.path.join(self.images_dir, 'val')
        self.test_images_dir = os.path.join(self.images_dir, 'test')
        
        self.train_labels_dir = os.path.join(self.labels_dir, 'train')
        self.val_labels_dir = os.path.join(self.labels_dir, 'val')
        self.test_labels_dir = os.path.join(self.labels_dir, 'test')
        
        self._create_directories()
        
    def _create_directories(self):
        os.makedirs(self.output_dir, exist_ok=True)
        
        for directory in [
            self.images_dir, self.labels_dir,
            self.train_images_dir, self.val_images_dir, self.test_images_dir,
            self.train_labels_dir, self.val_labels_dir, self.test_labels_dir
        ]:
            os.makedirs(directory, exist_ok=True)
    
    def _determine_bucket(self, annotations: List[Dict[str, Any]]) -> str:
        if not annotations:
            return self.train_images_dir
            
        sample = annotations[0]
        image_id = sample['ImageId']
        upload_id = sample['UploadId']
        grown_weed = sample['GrownWeed']
        
        if upload_id in FIXED_UPLOAD_IDS_TRAIN:
            return self.train_images_dir
        elif upload_id in FIXED_UPLOAD_IDS_VAL:
            return self.val_images_dir
        elif upload_id in FIXED_UPLOAD_IDS_TEST:
            return self.test_images_dir
        
        if image_id in FIXED_IMAGE_IDS_TRAIN:
            return self.train_images_dir
        elif image_id in FIXED_IMAGE_IDS_VAL:
            return self.val_images_dir
        elif image_id in FIXED_IMAGE_IDS_TEST:
            return self.test_images_dir
        
        if grown_weed:
            return self.train_images_dir
            
        bucket_paths = [self.train_images_dir, self.val_images_dir, self.test_images_dir]
        return np.random.choice(bucket_paths, p=self.bucket_prob / np.sum(self.bucket_prob))
    
    def _create_image_symlink(self, image_id: int, filename: str, bucket_path: str) -> str:
        source_dir = self.rwm_images_path
        source_path = os.path.join(source_dir, filename)
        
        _, ext = os.path.splitext(filename)
        dest_path = os.path.join(bucket_path, f"{image_id}{ext}")
        
        if not os.path.exists(source_path):
            print(f"Warning: Source image not found: {source_path}")
            return None
            
        if not os.path.exists(dest_path):
            os.symlink(source_path, dest_path)
            
        return dest_path
    
    def _create_label_file(self, annotations: List[Dict[str, Any]], image_path: str) -> str:
        if not image_path:
            return None
            
        images_dir, image_filename = os.path.split(image_path)
        image_name, _ = os.path.splitext(image_filename)
        
        labels_dir = images_dir.replace(os.path.join('images'), os.path.join('labels'))
        label_path = os.path.join(labels_dir, f"{image_name}.txt")
        
        yolo_lines = []
        for ann in annotations:
            yolo_line = convert_to_yolo_format(ann, self.eppo_codes)
            if yolo_line:
                yolo_lines.append(yolo_line)
        
        with open(label_path, 'w') as f:
            f.write('\n'.join(yolo_lines))
            
        return label_path
    
    def create_dataset_yaml(self) -> str:
        yaml_path = os.path.join(self.output_dir, 'dataset.yaml')
        
        data = {
            'path': self.output_dir,
            'train': os.path.join('images', 'train'),
            'val': os.path.join('images', 'val'),
            'test': os.path.join('images', 'test'),
            'nc': len(self.eppo_codes),
            'names': self.eppo_codes
        }
        
        with open(yaml_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
            
        return yaml_path
    
    def build_from_annotations(self, annotations: List[Dict[str, Any]]):
        print("Filtering out held back images...")
        annotations = [ann for ann in annotations if ann['ImageId'] not in IMAGE_IDS_HELD_BACK]
        
        print("Processing PSEZ annotations...")
        annotations = process_psez_annotations(annotations)
        
        print("Grouping annotations by image...")
        annotations_by_image = {}
        for ann in annotations:
            image_id = ann['ImageId']
            if image_id not in annotations_by_image:
                annotations_by_image[image_id] = []
            annotations_by_image[image_id].append(ann)
        
        print(f"Building dataset from {len(annotations_by_image)} images...")
        stats = {
            'train': 0,
            'val': 0,
            'test': 0,
            'skipped': 0,
            'total_annotations': len(annotations)
        }
        
        for image_id, image_annotations in annotations_by_image.items():
            bucket_path = self._determine_bucket(image_annotations)
            
            if not image_annotations:
                continue
                
            filename = image_annotations[0]['FileName']
            image_path = self._create_image_symlink(image_id, filename, bucket_path)
            
            if not image_path:
                stats['skipped'] += 1
                continue
                
            self._create_label_file(image_annotations, image_path)
            
            if bucket_path == self.train_images_dir:
                stats['train'] += 1
            elif bucket_path == self.val_images_dir:
                stats['val'] += 1
            elif bucket_path == self.test_images_dir:
                stats['test'] += 1
        
        print(f"Created dataset with {stats['train']} training, {stats['val']} validation, and {stats['test']} test images")
        print(f"Skipped {stats['skipped']} images (not found)")
        
        yaml_path = self.create_dataset_yaml()
        print(f"Created dataset YAML at {yaml_path}")
        
        return stats

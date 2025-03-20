import os
import numpy as np
import shutil
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

class YOLODatasetBuilder:
    def __init__(
            self,
            dataset_root: str,
            images_source_path: str,
            eppo_codes: List[str],
            image_ids_held_back: List[int],
            fixed_upload_ids_train: List[int],
            fixed_upload_ids_val: List[int],
            fixed_upload_ids_test: List[int],
            fixed_image_ids_train: List[int],
            fixed_image_ids_val: List[int],
            fixed_image_ids_test: List[int],
            bucket_prob: List[float]
        ):
        self.dataset_root = dataset_root
        self.images_source_path = images_source_path
        self.eppo_codes = eppo_codes
        self.image_ids_held_back = image_ids_held_back
        self.fixed_upload_ids_train = fixed_upload_ids_train
        self.fixed_upload_ids_val = fixed_upload_ids_val
        self.fixed_upload_ids_test = fixed_upload_ids_test
        self.fixed_image_ids_train = fixed_image_ids_train
        self.fixed_image_ids_val = fixed_image_ids_val
        self.fixed_image_ids_test = fixed_image_ids_test
        self.bucket_prob = np.array(bucket_prob)
        
        # Create dataset directory structure
        self.images_dir = os.path.join(self.dataset_root, 'images')
        self.labels_dir = os.path.join(self.dataset_root, 'labels')
        
        self.train_images_dir = os.path.join(self.images_dir, 'train')
        self.val_images_dir = os.path.join(self.images_dir, 'val')
        self.test_images_dir = os.path.join(self.images_dir, 'test')
        
        self.train_labels_dir = os.path.join(self.labels_dir, 'train')
        self.val_labels_dir = os.path.join(self.labels_dir, 'val')
        self.test_labels_dir = os.path.join(self.labels_dir, 'test')
        
        self.bucket_image_paths = [
            self.train_images_dir,
            self.val_images_dir,
            self.test_images_dir
        ]
        
    def setup_directories(self):
        # Create parent directories
        os.makedirs(self.dataset_root, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.labels_dir, exist_ok=True)
        
        # Create split directories
        for directory in [
            self.train_images_dir, self.val_images_dir, self.test_images_dir,
            self.train_labels_dir, self.val_labels_dir, self.test_labels_dir
        ]:
            os.makedirs(directory, exist_ok=True)
    
    def create_dataset_yaml(self):
        yaml_path = os.path.join(self.dataset_root, 'dataset.yaml')
        with open(yaml_path, 'w') as f:
            # Write class names
            f.write("names:\n")
            for eppo in self.eppo_codes:
                f.write(f"- {eppo}\n")
            
            # Write number of classes
            f.write(f"nc: {len(self.eppo_codes)}\n")
            
            # Write folder paths
            f.write(f"train: {self.train_images_dir}\n")
            f.write(f"val: {self.val_images_dir}\n")
            f.write(f"test: {self.test_images_dir}\n")
        
        return yaml_path
    
    def determine_bucket(self, annotations: List[Dict[str, Any]]) -> str:
        if not annotations:
            return self.train_images_dir
            
        sample_annotation = annotations[0]
        upload_id = sample_annotation['UploadId']
        image_id = sample_annotation['ImageId']
        grown_weed = sample_annotation['GrownWeed']
        
        # Check fixed upload IDs
        if upload_id in self.fixed_upload_ids_train:
            return self.train_images_dir
        elif upload_id in self.fixed_upload_ids_val:
            return self.val_images_dir
        elif upload_id in self.fixed_upload_ids_test:
            return self.test_images_dir
        
        # Check fixed image IDs
        if image_id in self.fixed_image_ids_train:
            return self.train_images_dir
        elif image_id in self.fixed_image_ids_val:
            return self.val_images_dir
        elif image_id in self.fixed_image_ids_test:
            return self.test_images_dir
        
        # Handle grown weed images
        if grown_weed:
            return self.train_images_dir
        
        # Random assignment based on probability
        return np.random.choice(self.bucket_image_paths, p=self.bucket_prob / self.bucket_prob.sum())
    
    def create_image_symlink(self, source_path: str, destination_dir: str, image_id: int) -> str:
        filename = os.path.basename(source_path)
        _, ext = os.path.splitext(filename)
        
        destination_path = os.path.join(destination_dir, f"{image_id}{ext}")
        os.symlink(source_path, destination_path)
        
        return destination_path
    
    def create_label_file(self, image_path: str, annotations: List[Dict[str, Any]], from_annotation_utils) -> str:
        # Find the corresponding label directory
        images_dir, image_filename = os.path.split(image_path)
        image_name, _ = os.path.splitext(image_filename)
        
        labels_dir = images_dir.replace('images', 'labels')
        label_path = os.path.join(labels_dir, f"{image_name}.txt")
        
        # Generate label content
        label_lines = []
        for annotation in annotations:
            yolo_line = from_annotation_utils.convert_to_yolo_format(annotation, self.eppo_codes)
            if yolo_line:
                label_lines.append(yolo_line)
        
        # Write label file
        with open(label_path, 'w') as f:
            f.write('\n'.join(label_lines))
        
        return label_path
    
    def process_annotations(self, annotations_by_image: Dict[int, List[Dict[str, Any]]], from_annotation_utils):
        total_images = len(annotations_by_image)
        print(f"Processing {total_images} images...")
        
        for image_id, annotations in annotations_by_image.items():
            if not annotations:
                continue
                
            # Determine which bucket (train/val/test) to put this image in
            bucket_dir = self.determine_bucket(annotations)
            
            # Get the source image path
            sample_annotation = annotations[0]
            filename = sample_annotation['FileName']
            upload_id = sample_annotation['UploadId']
            
            # Find correct source image path
            image_path = None
            for potential_path in [
                os.path.join(self.images_source_path, str(upload_id), filename),
                os.path.join(self.images_source_path, filename)
            ]:
                if os.path.exists(potential_path):
                    image_path = potential_path
                    break
            
            if not image_path:
                print(f"Warning: Could not find source image for ID: {image_id}, filename: {filename}")
                continue
            
            # Create symlink to the image
            image_symlink = self.create_image_symlink(image_path, bucket_dir, image_id)
            
            # Create label file
            self.create_label_file(image_symlink, annotations, from_annotation_utils)
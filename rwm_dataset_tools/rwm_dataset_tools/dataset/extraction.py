"""
Dataset extraction from RWM database to YOLO format.
"""
import os
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from tqdm import tqdm

from rwm_dataset_tools.database.connection import RWMDatabase
from rwm_dataset_tools.database.queries import RWMDataExtractor
from rwm_dataset_tools.dataset.processing import partition_by_image_id, process_psez_annotations, determine_dataset_split

logger = logging.getLogger(__name__)

class DatasetExtractor:
    """
    Extract dataset from RWM database and prepare it in the required format.
    """
    def __init__(self, config: Dict[str, Any], format_handler):
        """
        Initialize the dataset extractor.
        
        Args:
            config: Configuration dictionary
            format_handler: Format handler instance (e.g., YOLOv11Format)
        """
        self.config = config
        self.format_handler = format_handler
        self.db = RWMDatabase(config['database'])
        self.data_extractor = RWMDataExtractor(self.db, config)
        
        # For reproducibility
        self.random_seed = config.get('random_seed', 42)
        self.rng = np.random.RandomState(self.random_seed)
        
    def extract(self) -> Dict[str, int]:
        """
        Extract dataset from RWM database and prepare it in the required format.
        
        Returns:
            Dictionary with statistics about the extracted dataset
        """
        logger.info("Starting dataset extraction")
        
        # Connect to the database
        with self.db:
            # Get annotation data
            data = self.data_extractor.get_annotation_data()
            
            # Filter out held back images
            data = self.data_extractor.filter_held_back_images(data)
            
            # Process PSEZ annotations
            data = process_psez_annotations(data, self.config['dataset']['psez_crops'])
            
            # Partition data by image ID
            logger.info("Partitioning data by image ID")
            data_by_image = partition_by_image_id(data)
            
            # Create dataset files
            stats = self._create_dataset_files(data_by_image)
            
            # Create dataset YAML file
            yaml_path = self.format_handler.create_dataset_yaml()
            logger.info(f"Created dataset YAML file: {yaml_path}")
            
        return stats
        
    def _create_dataset_files(self, data_by_image: Dict[int, pd.DataFrame]) -> Dict[str, int]:
        """
        Create dataset files (images and labels) for each image.
        
        Args:
            data_by_image: Dictionary mapping image IDs to DataFrames with annotations
            
        Returns:
            Dictionary with statistics about the created files
        """
        # Initialize statistics
        stats = {
            'total_images': len(data_by_image),
            'train_images': 0,
            'val_images': 0,
            'test_images': 0,
            'total_annotations': 0,
            'train_annotations': 0,
            'val_annotations': 0,
            'test_annotations': 0
        }
        
        # Process each image
        logger.info(f"Creating dataset files for {len(data_by_image)} images")
        for image_id, annotations in tqdm(data_by_image.items(), desc="Processing images"):
            # Determine dataset split
            split = determine_dataset_split(annotations, self.config, self.rng)
            
            # Get image path
            row = annotations.iloc[0]
            upload_id = row['UploadId']
            filename = row['FileName']
            
            # Get full image path
            source_path = self.data_extractor.get_image_path(upload_id, filename)
            
            # Create image symlink
            self.format_handler.create_image_symlink(source_path, image_id, split)
            
            # Create label file
            self.format_handler.create_label_file(annotations, image_id, split)
            
            # Update statistics
            stats[f'{split}_images'] += 1
            stats[f'{split}_annotations'] += len(annotations)
            stats['total_annotations'] += len(annotations)
            
        return stats
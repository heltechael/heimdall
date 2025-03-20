"""
SQL queries and data fetching for the RWM database.
"""
import pandas as pd
import logging
from typing import Dict, Any, List, Optional, Tuple

from rwm_dataset_tools.database.connection import RWMDatabase

logger = logging.getLogger(__name__)

class RWMDataExtractor:
    """
    Class to extract annotation and image data from the RWM database.
    """
    def __init__(self, db: RWMDatabase, config: Dict[str, Any]):
        """
        Initialize the data extractor.
        
        Args:
            db: Database connection
            config: Configuration dictionary
        """
        self.db = db
        self.config = config
        
    def get_annotation_data(self) -> pd.DataFrame:
        """
        Get annotation data for training, following the same logic as the I-GIS scripts.
        This query replicates the logic in the get_labled_data_annotation method.
        
        Returns:
            DataFrame with annotation data
        """
        # Define blacklist plant IDs - typically these would come from configuration
        blacklist_plant_ids = [-12, -7, 0, 148, 150, 151, 994]  # Same as in blacklist_plant_ids_annotation.csv
        
        # Format the blacklist for SQL
        blacklist_str = ', '.join(str(id) for id in blacklist_plant_ids)
        
        # Build the query - this replicates the logic in rwm_db.get_labled_data_annotation()
        query = f"""
        SELECT
            [data].[AnnotationData].[Id],
            [UploadId],
            [FileName],
            [ImageId],
            [PlantId],
            TRIM([data].[PlantInfo].[EPPOCode]) AS EPPOCode,
            [NameEnglish],
            [GrowthStage],
            [Width],
            [Height],
            [PolyData],
            [BrushSize],
            [MinX],
            [MinY],
            [MaxX],
            [MaxY],
            [AnnotationModelId],
            [UseForTraining],
            [ClassificationModelId],
            [Approved],
            [GrownWeed],
            [cotyledon]
         FROM
            [data].[Images]
            INNER JOIN [data].[Annotations] ON ([data].[Annotations].[ImageId] = [data].[Images].[Id])
            LEFT JOIN [data].[AnnotationData] ON ([data].[AnnotationData].[AnnotationId] = [data].[Images].[Id])
            LEFT JOIN [data].[PlantInfo] ON ([AnnotationData].[PlantId] = [data].[PlantInfo].[Id])
            LEFT JOIN [data].[Uploads]  ON ([data].[Images].[UploadId] = [data].[Uploads].[Id])
         WHERE
            [data].[Images].[IsDeleted] = 0
            AND [data].[Uploads].[IsDeleted] = 0
            AND ([data].[AnnotationData].IsTemporary = 0 OR [data].[AnnotationData].IsTemporary is NULL)
            AND [data].[Annotations].[UseForTraining] = 1
            AND [data].[AnnotationData].[PlantId] NOT IN ({blacklist_str})
        """
        
        logger.info("Fetching annotation data from database...")
        data = self.db.execute_query(query)
        logger.info(f"Fetched {len(data)} annotation records")
        return data
        
    def filter_held_back_images(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Filter out held back images from the dataset.
        
        Args:
            data: DataFrame with annotation data
            
        Returns:
            Filtered DataFrame
        """
        held_back_images = self.config['dataset']['held_back_images']
        before_len = len(data)
        data = data[~data['ImageId'].isin(held_back_images)]
        logger.info(f"Filtered out held back images: {before_len} -> {len(data)} annotations")
        return data
        
    def get_upload_ids_for_image_ids(self, image_ids: List[int]) -> Dict[int, int]:
        """
        Get upload IDs for a list of image IDs.
        
        Args:
            image_ids: List of image IDs
            
        Returns:
            Dictionary mapping image IDs to upload IDs
        """
        # Convert list to string for IN clause
        image_ids_str = ', '.join(str(id) for id in image_ids)
        
        query = f"""
        SELECT [Id] AS ImageId, [UploadId]
        FROM [data].[Images]
        WHERE [Id] IN ({image_ids_str})
        """
        
        result = self.db.execute_query(query)
        return dict(zip(result['ImageId'], result['UploadId']))
        
    def get_image_path(self, upload_id: int, filename: str) -> str:
        """
        Get the full path to an image.
        
        Args:
            upload_id: Upload ID
            filename: Filename
            
        Returns:
            Full path to the image
        """
        rwm_data_path = self.config['paths']['rwm_data']
        return f"{rwm_data_path}/{upload_id}/{filename}"
import pymssql
import os
from typing import List, Dict, Any, Optional

class RWMDatabaseConnector:
    def __init__(self, db_name='RoboWeedMaps', host='localhost', user='SA', password='Robotbil123!'):
        self.db_name = db_name
        self.host = host
        self.user = user
        self.password = password
        self.conn = None
        
    def connect(self):
        self.conn = pymssql.connect(
            server=self.host,
            user=self.user,
            password=self.password,
            database=self.db_name
        )
        return self.conn
    
    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            
    def get_training_annotations(self) -> List[Dict[str, Any]]:
        if not self.conn:
            self.connect()
            
        cursor = self.conn.cursor(as_dict=True)
        
        query = """
        SELECT 
            a.Id,
            a.EPPOCode,
            a.ImageId,
            a.MinX, a.MinY, a.MaxX, a.MaxY,
            i.Width, i.Height, i.FileName,
            i.UploadId,
            ISNULL(p.GrownPlant, 0) as GrownWeed,
            ISNULL(a.cotyledon, 0) as cotyledon,
            a.APPROVED
        FROM data.Annotations a
        INNER JOIN data.Images i ON a.ImageId = i.Id
        LEFT JOIN data.Plants p ON a.PlantId = p.Id
        WHERE i.USE_FOR_TRAINING = 1
        """
        
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        
        return result

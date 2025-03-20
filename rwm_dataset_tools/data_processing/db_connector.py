import pyodbc
from typing import Dict, List, Any, Optional

class RWMDatabase:
    def __init__(self, db_name: str = "RoboWeedMaps", server: str = "localhost", user: str = "SA", password: str = "Robotbil123!"):
        self.conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={db_name};"
            f"UID={user};"
            f"PWD={password};"
        )
        
    def connect(self):
        return pyodbc.connect(self.conn_str)
        
    def get_labeled_data_for_training(self) -> List[Dict[str, Any]]:
        query = """
        SELECT 
            a.Id,
            a.ImageId,
            a.MinX,
            a.MinY,
            a.MaxX,
            a.MaxY,
            a.EPPOCode,
            a.Cotyledon as cotyledon,
            i.FileName,
            i.Width,
            i.Height,
            i.UploadId,
            u.GrownWeed
        FROM data.Annotations a
        JOIN data.Images i ON a.ImageId = i.Id
        JOIN data.Uploads u ON i.UploadId = u.Id
        WHERE i.UseForTraining = 1
        """
        
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(query)
            
            columns = [column[0] for column in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
                
            conn.close()
            return results
            
        except Exception as e:
            print(f"Database error: {e}")
            return []
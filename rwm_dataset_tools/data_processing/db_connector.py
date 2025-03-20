import pyodbc
from config.dataset_config import DATABASE_NAME

class RoboWeedMaPSDB:
    def __init__(self, db: str = DATABASE_NAME):
        self.db = db
        self.conn = self._get_connection()

    def _get_connection(self):
        conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=localhost;"
            f"DATABASE={self.db};"
            "UID=SA;"
            "PWD=Robotbil123!;"
        )
        return pyodbc.connect(conn_str)

    def get_labled_data_annotation(self):
        query = """
        SELECT 
            a.Id,
            a.ImageId,
            a.UploadId,
            i.FileName,
            a.EPPOCode,
            a.MinX,
            a.MinY,
            a.MaxX,
            a.MaxY,
            i.Width,
            i.Height,
            i.GrownWeed,
            a.cotyledon
        FROM data.Annotations a
        JOIN data.Images i ON a.ImageId = i.Id
        WHERE a.[USE FOR TRAINING] = 1 AND a.APPROVED = 1
        """
        cursor = self.conn.cursor()
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return data

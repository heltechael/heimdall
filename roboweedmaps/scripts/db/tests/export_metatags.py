import pyodbc
import pandas as pd
import os
from datetime import datetime

# Connection string
conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=RoboWeedMaps;"
    "UID=SA;"
    "PWD=Robotbil123!;"
)

# Output file name with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"metatags_export_{timestamp}.csv"

try:
    # Connect to the database
    print("Connecting to the database...")
    conn = pyodbc.connect(conn_str)
    
    # Create SQL query - note we're selecting ALL rows, not just 1000
    query = """
    SELECT 
        [Id],
        [TagLabel],
        [TagLabelNormalized],
        [AddTime]
    FROM [RoboWeedMaps].[data].[MetaTags]
    """
    
    print("Executing query to fetch all MetaTags...")
    # Read directly into a pandas DataFrame
    df = pd.read_sql(query, conn)
    
    # Get row count
    row_count = len(df)
    print(f"Successfully retrieved {row_count} MetaTags records")
    
    # Save to CSV
    print(f"Saving data to {output_file}...")
    df.to_csv(output_file, index=False)
    
    # Close the connection
    conn.close()
    
    print(f"Export complete! File saved to: {os.path.abspath(output_file)}")
    print(f"Total records exported: {row_count}")
    
except Exception as e:
    print(f"Error: {e}")

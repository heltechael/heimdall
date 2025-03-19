import pyodbc
import pandas as pd
import os
from datetime import datetime
import time

# Connection string
conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=RoboWeedMaps;"
    "UID=SA;"
    "PWD=Robotbil123!;"
)

# Output file names with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
uploads_file = f"uploads_export_{timestamp}.csv"
image_counts_file = f"upload_image_counts_{timestamp}.csv"

try:
    # Connect to the database
    print("Connecting to the database...")
    conn = pyodbc.connect(conn_str)
    
    # Step 1: Export all Uploads
    uploads_query = """
    SELECT 
        [Id],
        [FieldId],
        [Name],
        [UploadDate],
        [UserId],
        [IsDeleted],
        [LockedBySystem],
        [GrownWeed]
    FROM [RoboWeedMaps].[data].[Uploads]
    """
    
    print("Executing query to fetch all Uploads...")
    start_time = time.time()
    uploads_df = pd.read_sql(uploads_query, conn)
    query_time = time.time() - start_time
    
    # Get row count
    uploads_count = len(uploads_df)
    print(f"Successfully retrieved {uploads_count} Uploads records in {query_time:.2f} seconds")
    
    # Save Uploads to CSV
    print(f"Saving Uploads data to {uploads_file}...")
    uploads_df.to_csv(uploads_file, index=False)
    print(f"Uploads export complete!")
    
    # Step 2: Create summary of image counts per upload
    image_counts_query = """
    SELECT 
        u.[Id] AS UploadId,
        u.[Name] AS UploadName,
        u.[UploadDate],
        u.[FieldId],
        COUNT(i.[Id]) AS ImageCount
    FROM [RoboWeedMaps].[data].[Uploads] u
    LEFT JOIN [RoboWeedMaps].[data].[Images] i ON u.[Id] = i.[UploadId]
    WHERE i.[IsDeleted] = 0 OR i.[IsDeleted] IS NULL
    GROUP BY u.[Id], u.[Name], u.[UploadDate], u.[FieldId]
    ORDER BY u.[UploadDate] DESC
    """
    
    print("Calculating image counts per upload...")
    start_time = time.time()
    image_counts_df = pd.read_sql(image_counts_query, conn)
    query_time = time.time() - start_time
    
    # Get summary stats
    summary_count = len(image_counts_df)
    total_images = image_counts_df['ImageCount'].sum()
    print(f"Generated summary for {summary_count} uploads with a total of {total_images} images in {query_time:.2f} seconds")
    
    # Save image counts to CSV
    print(f"Saving image counts data to {image_counts_file}...")
    image_counts_df.to_csv(image_counts_file, index=False)
    
    # Close the connection
    conn.close()
    
    # Print final summary
    print("\nExport Summary:")
    print(f"1. Uploads export: {uploads_count} records saved to {os.path.abspath(uploads_file)}")
    print(f"2. Image counts: {summary_count} uploads with {total_images} total images saved to {os.path.abspath(image_counts_file)}")
    
except Exception as e:
    print(f"Error: {e}")

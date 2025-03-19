import pyodbc
import pandas as pd

# Connection string
conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=RoboWeedMaps;"
    "UID=SA;"
    "PWD=Robotbil123!;"
)

try:
    # Connect to the database
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    # Get table list with schema names
    cursor.execute("SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
    tables = [(row[0], row[1]) for row in cursor.fetchall()]
    
    print("Successfully connected to the database!")
    print(f"Found {len(tables)} tables:")
    for schema, table in tables[:1000]:  # Show first 10 tables
        print(f"- {schema}.{table}")
    
    if len(tables) > 0:
        # Get sample data from first table
        schema, table = tables[0]
        print(f"\nFetching sample data from '{schema}.{table}':")
        sample_query = f"SELECT TOP 5 * FROM {schema}.{table}"
        df = pd.read_sql(sample_query, conn)
        print(df)
    
    # Close the connection
    conn.close()
    
except Exception as e:
    print(f"Error connecting to database: {e}")

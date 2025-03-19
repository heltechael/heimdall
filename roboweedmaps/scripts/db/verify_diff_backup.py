import pyodbc
import pandas as pd
from datetime import datetime
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="pandas.io.sql")

# Connection string
conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=RoboWeedMapsTest;"  # Changed to your test database
    "UID=SA;"
    "PWD=Robotbil123!;"
)

try:
    # Connect to the database
    print(f"Connecting to database at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    # Get database basic information
    print("\n=== Database Information ===")
    cursor.execute("""
    SELECT 
        d.name AS DatabaseName,
        d.create_date AS DatabaseCreationDate,
        d.state_desc AS DatabaseState
    FROM sys.databases d
    WHERE d.name = 'RoboWeedMapsTest'
    """)
    
    db_info = cursor.fetchone()
    if db_info:
        print(f"Database Name: {db_info.DatabaseName}")
        print(f"Creation Date: {db_info.DatabaseCreationDate}")
        print(f"Current State: {db_info.DatabaseState}")
    
    # Get table list
    cursor.execute("SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
    tables = [(row[0], row[1]) for row in cursor.fetchall()]
    
    print(f"\nFound {len(tables)} tables in the database")
    
    # Print some tables from the database
    print("\n=== Sample Tables ===")
    for i, (schema, table) in enumerate(tables[:10]):
        print(f"{i+1}. {schema}.{table}")
    
    # Check for time-related columns in key tables
    print("\n=== Recent Data Analysis ===")
    time_tables = []
    
    # Look for tables with timestamp or date columns
    for schema, table in tables:
        cursor.execute(f"""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = '{schema}' 
        AND TABLE_NAME = '{table}'
        AND (DATA_TYPE LIKE '%date%' OR DATA_TYPE LIKE '%time%')
        """)
        date_columns = [row[0] for row in cursor.fetchall()]
        
        if date_columns:
            time_tables.append((schema, table, date_columns[0]))
    
    # Get most recent records from tables with timestamps
    for schema, table, date_column in time_tables[:5]:  # Check first 5 tables with timestamps
        try:
            query = f"""
            SELECT TOP 5 * 
            FROM {schema}.{table} 
            ORDER BY {date_column} DESC
            """
            df = pd.read_sql(query, conn)
            
            if not df.empty:
                most_recent = df.iloc[0][date_column]
                print(f"\nMost recent record in {schema}.{table}:")
                print(f"  Date Column: {date_column}")
                print(f"  Most Recent: {most_recent}")
                print(f"  Record Count: {pd.read_sql(f'SELECT COUNT(*) AS count FROM {schema}.{table}', conn).iloc[0]['count']}")
        except Exception as e:
            print(f"Error analyzing {schema}.{table}: {e}")
    
    # Special check for uploads, images, or annotations tables
    key_tables = [t for t in tables if t[1].lower() in ('uploads', 'images', 'annotations', 'metatags')]
    if key_tables:
        print("\n=== Key Tables Analysis ===")
        for schema, table in key_tables[:3]:  # Check first 3 key tables
            try:
                count = pd.read_sql(f'SELECT COUNT(*) AS count FROM {schema}.{table}', conn).iloc[0]['count']
                print(f"{schema}.{table}: {count} records")
                
                # Try to get the most recent record based on ID
                cursor.execute(f"""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = '{schema}' 
                AND TABLE_NAME = '{table}'
                AND COLUMN_NAME = 'Id'
                """)
                
                if cursor.fetchone():
                    max_id = pd.read_sql(f'SELECT MAX(Id) AS max_id FROM {schema}.{table}', conn).iloc[0]['max_id']
                    print(f"  Maximum ID: {max_id}")
            except Exception as e:
                print(f"Error analyzing {schema}.{table}: {e}")
    
    # Close the connection
    conn.close()
    print("\nAnalysis complete!")
    
except Exception as e:
    print(f"Error connecting to database: {e}")

import pyodbc

def get_connection(server, db_name, user, password):
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=" + server + ";"
        "DATABASE=" + db_name + ";"
        "UID=" + user + ";"
        "PWD=" + password + ";"
    )
    return pyodbc.connect(conn_str)
    
def fetch_annotations(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM [data].[Annotations] WHERE [UseForTraining]=1")
    return [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]

def fetch_image_info(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM [data].[Images] WHERE [IsDeleted]=0")
    return [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]

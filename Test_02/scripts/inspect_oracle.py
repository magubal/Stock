
import cx_Oracle
import os

# Connection details
# Host (IP): localhost
# port : 1521
# SID : orcl
# username : psj
# password : wns0412

# Create connection string - Try Easy Connect format
# dsn = oracledb.makedsn("localhost", 1521, sid="orcl")
dsn = "localhost:1521/orcl"

try:
    connection = cx_Oracle.connect(
        user="psj",
        password="wns0412",
        dsn=dsn
    )
    print("✅ Successfully connected to Oracle Database")

    cursor = connection.cursor()
    
    # Inspect table schema
    table_name = "FN_JEJO_LOAD"
    print(f"\n🔍 Inspecting table: {table_name}")
    
    # Get column info
    cursor.execute(f"SELECT column_name, data_type, data_length FROM user_tab_columns WHERE table_name = '{table_name}' ORDER BY column_id")
    columns = cursor.fetchall()
    
    print(f"{'Column Name':<30} | {'Type':<15} | {'Length'}")
    print("-" * 60)
    for col in columns:
        print(f"{col[0]:<30} | {col[1]:<15} | {col[2]}")

    # Inspect first 5 rows to see data format
    print(f"\n📄 Sample Data (First 5 rows):")
    cursor.execute(f"SELECT * FROM {table_name} FETCH FIRST 5 ROWS ONLY")
    rows = cursor.fetchall()
    
    # Print column headers first
    col_names = [col[0] for col in cursor.description]
    print(col_names)
    
    for row in rows:
        print(row)

    connection.close()

except cx_Oracle.Error as e:
    print(f"❌ Oracle Error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")

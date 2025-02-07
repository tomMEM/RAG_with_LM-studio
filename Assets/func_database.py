import sqlite3
import pandas as pd

def database_inspector(database_name, table_name):
    """
    Comprehensive database inspection and querying utility
    """
    try:
        # Connect to the database
        conn = sqlite3.connect(database_name)
        
        # Database Overview
        print("\n" + "="*50)
        print(f"DATABASE INSPECTOR: {database_name}")
        print("="*50)
        
        # 1. Table Information
        print("\n1. TABLE STRUCTURE:")
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        for col in columns:
            print(f"Column {col[0]}: {col[1]} ({col[2]})")
        
        # 2. Record Count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        record_count = cursor.fetchone()[0]
        print(f"\n2. TOTAL RECORDS: {record_count}")
        
        # 3. Quick Data Overview
        print("\n3. DATA SAMPLE (First 5 Records):")
        df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 15", conn)
        print(df)
        
        # 4. Metadata Summary
        print("\n4. METADATA SUMMARY:")
        summary_queries = {
            "Unique Authors": f"SELECT COUNT(DISTINCT Authors) FROM {table_name}",
            "Publication Date": f"SELECT DISTINCT Date FROM {table_name} ORDER BY Date",
            "Journals": f"SELECT DISTINCT Journal FROM {table_name}"
        }
        
        for query_name, query in summary_queries.items():
            cursor.execute(query)
            results = cursor.fetchall()
            print(f"{query_name}: {results}")
        
        # 5. Advanced Filtering Options
        print("\n5. FILTERING OPTIONS:")
        filter_options = [
            ("Recent Publications", f"SELECT Title, Date FROM {table_name} ORDER BY Date DESC LIMIT 5"),
            ("Longest Abstracts", f"SELECT Title, LENGTH(Abstract) as AbsLength FROM {table_name} ORDER BY AbsLength DESC LIMIT 5")
        ]
        
        for option_name, query in filter_options:
            print(f"\n{option_name}:")
            df = pd.read_sql_query(query, conn)
            print(df)
        
        # Interactive Query Prompt
        while True:
            print("\n6. INTERACTIVE SQL QUERY")
            custom_query = input("Enter a custom SQL query (or 'exit' to quit): ")
            
            if custom_query.lower() == 'exit':
                break
            
            try:
                df = pd.read_sql_query(custom_query, conn)
                print("\nQUERY RESULTS:")
                print(df)
            except Exception as e:
                print(f"Error executing query: {e}")
        
        # Close connection
        conn.close()
    
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def database_structure(database_name):
    
    
    # Option to inspect database
    inspect_db = input("Would you like to inspect the database? (y/n): ").lower()
    if inspect_db == 'y':
        #database_name = input("Enter the database name: ")
        #table_name = input("Enter the table name: ")
        conn = sqlite3.connect(database_name)
        cursor = conn.cursor()

        # Check if the table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        result = cursor.fetchone()
        table_name = result[0]
        database_inspector(database_name, table_name)


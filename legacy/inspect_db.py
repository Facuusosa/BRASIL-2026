import sqlite3

DB_PATH = 'flybondi_monitor.db'

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("--- Columns in flight_history ---")
    cursor.execute(f"PRAGMA table_info(flight_history)")
    columns = cursor.fetchall()
    cols = []
    for col in columns:
        print(col)
        cols.append(col[1])
            
    print("\n--- Identifying price and date columns ---")
    # I suspect:
    # date_out, date_in?
    # let's look at the columns printed above.
    
    # Just select * and print one row as dict
    cursor.execute("SELECT * FROM flight_history LIMIT 1")
    row = cursor.fetchone()
    if row:
        row_dict = dict(zip(cols, row))
        print(row_dict)
        
    print("\n--- Lowest Price Search ---")
    # Assuming 'total_price' exists (from previous run output: (6, 'total_price', ...))
    # Select min price
    cursor.execute("SELECT MIN(total_price), currency FROM flight_history GROUP BY currency")
    mins = cursor.fetchall()
    print("Minimum prices found by currency:", mins)

    
    conn.close()

except Exception as e:
    print(f"Error: {e}")

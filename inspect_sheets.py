import pandas as pd

path_cod = r"c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\data\raw\CODIGOS.xlsx"

try:
    with pd.ExcelWriter("temp_inspection.xlsx") as writer: # Not really needed, just using it to read
        pass
    
    xl = pd.ExcelFile(path_cod)
    for sheet in ['YAGUAR', 'MAXICONSUMO']:
        if sheet in xl.sheet_names:
            df = pd.read_excel(path_cod, sheet_name=sheet, nrows=5)
            print(f"\n--- {sheet} Sheet ---")
            print(f"Columns: {df.columns.tolist()}")
            print(df.head(3).to_string())
        else:
            print(f"\nSheet {sheet} not found.")

except Exception as e:
    print(f"Error: {e}")

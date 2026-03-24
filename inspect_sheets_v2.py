import pandas as pd

path_cod = r"c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\data\raw\CODIGOS.xlsx"

try:
    xl = pd.ExcelFile(path_cod)
    print(f"Sheets: {xl.sheet_names}")
    for sheet in xl.sheet_names:
        df = pd.read_excel(path_cod, sheet_name=sheet, nrows=2)
        print(f"\n--- {sheet} ---")
        print(df.columns.tolist())
        print(df.head(1).to_string())
except Exception as e:
    print(f"Error: {e}")

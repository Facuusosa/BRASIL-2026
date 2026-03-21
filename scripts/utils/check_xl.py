
import pandas as pd

try:
    xl = pd.ExcelFile(r"c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\Precios competidores.xlsx")
    print(f"Sheets: {xl.sheet_names}")
    for sheet in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=sheet)
        print(f"\nSheet Index: {sheet}")
        print(df.head())
        print(f"Rows: {len(df)}")
except Exception as e:
    print(f"Error: {e}")

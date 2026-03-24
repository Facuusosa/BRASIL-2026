import pandas as pd

path_cod = r"c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\data\raw\CODIGOS.xlsx"

try:
    for sheet in ['YAGUAR', 'MAXICONSUMO']:
        df = pd.read_excel(path_cod, sheet_name=sheet, nrows=2)
        print(f"\n--- {sheet} ---")
        print(f"Columns: {df.columns.tolist()}")
        print(df.iloc[:1].to_string())
except Exception as e:
    print(f"Error in sheet {sheet}: {e}")

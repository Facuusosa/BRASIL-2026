import pandas as pd
import sys

try:
    path_cod = r"c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\data\raw\CODIGOS.xlsx"
    df_cod = pd.read_excel(path_cod, nrows=0)
    print(f"CODIGOS.xlsx Columns: {df_cod.columns.tolist()}")
    
    path_mast = r"c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\data\raw\Listado Maestro 09-03.xlsx"
    df_mast = pd.read_excel(path_mast, nrows=0)
    print(f"Listado Maestro Columns: {df_mast.columns.tolist()}")
    
    # Check if there's a specific sheet or column for each wholesaler
    xl = pd.ExcelFile(path_cod)
    print(f"Sheets in CODIGOS: {xl.sheet_names}")
    
except Exception as e:
    print(f"Error: {e}")

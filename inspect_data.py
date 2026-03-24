import pandas as pd
import sys

try:
    file_path = r"c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\data\raw\CODIGOS.xlsx"
    df = pd.read_excel(file_path, nrows=5)
    print("--- CODIGOS.xlsx ---")
    print(df.to_string())
    
    file_path_master = r"c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\data\raw\Listado Maestro 09-03.xlsx"
    df_master = pd.read_excel(file_path_master, nrows=5)
    print("\n\n--- Listado Maestro ---")
    print(df_master.to_string())
except Exception as e:
    print(f"Error: {e}")

import pandas as pd
import os

f2 = r"c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\VITAL-all-products-20250921.xlsx"

try:
    df = pd.read_excel(f2, nrows=3)
    print("VITAL-ALL COLUMNS:", df.columns.tolist())
    print("VITAL-ALL SAMPLE:", df.to_string())
    # Count rows using pandas just for this test if it's not too slow
    # actually I won't count.
except Exception as e:
    print("ERROR:", e)

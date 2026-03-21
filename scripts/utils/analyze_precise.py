import pandas as pd
import os

f1 = r"c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\Copia de VITAL2-nini-products-20250921.xlsx"
f2 = r"c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\VITAL-all-products-20250921.xlsx"

def analyze_very_small(path, label):
    print(f"\n--- {label} ---")
    try:
        df = pd.read_excel(path, nrows=3)
        print(f"COLUMNS:")
        for c in df.columns:
            print(f"  - {c}")
        print(f"SAMPLE:")
        # We handle EAN as string so it doesn't show in scientific notation
        if 'ean' in [c.lower() for c in df.columns]:
            ean_col = [c for c in df.columns if c.lower() == 'ean'][0]
            df[ean_col] = df[ean_col].astype(str)
        print(df.head(3).to_string())
    except Exception as e:
        print("ERROR:", e)

analyze_very_small(f1, "VITAL2-nini (987 KB)")
analyze_very_small(f2, "VITAL-all (91 MB)")


import pandas as pd
import os

file_path = 'Precios competidores.xlsx'

if not os.path.exists(file_path):
    print(f"Error: El archivo {file_path} no existe.")
else:
    try:
        # Intentar leer metadatos de las hojas disponibles
        xls = pd.ExcelFile(file_path)
        print(f"📄 Hojas encontradas: {xls.sheet_names}")
        
        # Leer la primera hoja para ver encabezados y estructura
        df_raw = pd.read_excel(file_path, sheet_name=xls.sheet_names[0], header=None, nrows=15)
        print("\n=== Primeras 15 filas crudas (Hoja 1) ===")
        print(df_raw)
        
        # Intentar detectar si hay celdas con texto específico que indique "Oferta" o "Lista"
        print("\n=== Búsqueda de palabras clave 'Oferta' / 'Lista' ===")
        found_keywords = False
        for i, row in df_raw.iterrows():
            row_str = row.astype(str).str.lower().tolist()
            if any("oferta" in s for s in row_str) or any("lista" in s for s in row_str):
                print(f"⚠️ Palabra clave encontrada en fila {i}: {row.tolist()}")
                found_keywords = True
        
        if not found_keywords:
            print("No se detectaron palabras clave de 'Oferta' o 'Lista' en las primeras filas.")

    except Exception as e:
        print(f"Error al analizar el archivo: {e}")

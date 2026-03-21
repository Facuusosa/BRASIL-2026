
import pandas as pd
file_path = 'Precios competidores.xlsx'
df = pd.read_excel(file_path, sheet_name='SAP Document Export')

print("=== Análisis de Competidores Únicos ===")
print(df['COMPETIDOR'].unique())

print("\n=== Análisis de Tipos de Lista ===")
print(df['Tipo de lista de precios'].value_counts())

print("\n=== Ejemplo de un material duplicado (Varios competidores) ===")
# Tomar un material que aparezca varias veces
material_ejemplo = df['Material'].value_counts().index[0]
print(df[df['Material'] == material_ejemplo][['Material', 'Descripción de Material', 'COMPETIDOR', 'Precio', 'Tipo de lista de precios']])

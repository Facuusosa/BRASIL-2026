import json
import os

path = r"c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\BRUJULA-DE-PRECIOS\data\processed\catalogo_unificado.json"

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

unique = len(data)
multi = sum(1 for p in data if sum(1 for v in p["precios"].values() if v > 0) >= 2)
# Since I don't have a flag in the final JSON for "master_name", I'll just rely on the script's output if I can get it.
# Or I can re-run and print it clearly.

print(f"Productos únicos: {unique}")
print(f"Productos con 2+ mayoristas: {multi}")

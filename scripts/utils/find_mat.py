
import openpyxl
import os

def find_mat(mat_id):
    current_dir = os.getcwd()
    path = os.path.join(current_dir, "VITAL-all-products-20250921.xlsx")
    if not os.path.exists(path):
        print(f"Error: {path} no existe")
        return

    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    header = next(rows)
    mat_idx = header.index("Material")
    name_idx = header.index("productName")
    ean_idx = header.index("ean")
    sector_idx = header.index("sector")
    cat_idx = header.index("categories") if "categories" in header else header.index("Depto")

    print(f"Buscando Material {mat_id}...")
    for r in rows:
        # Check if r[mat_idx] is not None
        if r[mat_idx] is None: continue
        if str(r[mat_idx]) == str(mat_id):
            print(f"ENCONTRADO!")
            print(f"Nombre: {r[name_idx]}")
            print(f"EAN: {r[ean_idx]}")
            print(f"Sector: {r[sector_idx]}")
            print(f"Categoría: {r[cat_idx]}")
            return
    print("No se encontró.")

find_mat(22073)
find_mat(322)
find_mat(20019)

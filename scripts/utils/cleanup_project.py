import os
import shutil
import glob

# Paths
ROOT = os.getcwd()
DATA_RAW = os.path.join(ROOT, "data", "raw")
DATA_PROCESSED = os.path.join(ROOT, "data", "processed")
SCRIPTS_CORE = os.path.join(ROOT, "scripts", "core")
SCRIPTS_UTILS = os.path.join(ROOT, "scripts", "utils")
DOCS_MANIFESTOS = os.path.join(ROOT, "docs", "manifestos")
DOCS_REPORTS = os.path.join(ROOT, "docs", "reports")
ARCHIVE = os.path.join(ROOT, "archive")
EXTERNAL = os.path.join(ROOT, "external")

def make_dirs():
    for d in [DATA_RAW, DATA_PROCESSED, SCRIPTS_CORE, SCRIPTS_UTILS, DOCS_MANIFESTOS, DOCS_REPORTS, ARCHIVE, EXTERNAL]:
        os.makedirs(d, exist_ok=True)

def move_files():
    # 1. Manifestos (01_... to 07_...)
    for f in glob.glob("0[1-7]_*.md"):
        print(f"Moving {f} to docs/manifestos/")
        shutil.move(f, os.path.join(DOCS_MANIFESTOS, f))
    
    # 2. Excels and CSVs
    for ext in ["*.xlsx", "*.csv"]:
        for f in glob.glob(ext):
            print(f"Moving {f} to data/raw/")
            shutil.move(f, os.path.join(DATA_RAW, f))
            
    # 3. Core Engine
    if os.path.exists("engine_precios.py"):
        print("Moving engine_precios.py to scripts/core/")
        shutil.move("engine_precios.py", os.path.join(SCRIPTS_CORE, "engine_precios.py"))

    # 4. Utility Scripts
    utility_scripts = [
        "analyze_excel.py", "analyze_precise.py", "analyze_to_file.py", 
        "analyze_vertical.py", "check_xl.py", "cross_reference_ean.py", 
        "debug_ean.py", "enricher.py", "enricher_fuzzy.py", 
        "find_ean_on_site.py", "find_mat.py", "inspect_new_excel.py", 
        "test_vital_all.py", "cleanup.py"
    ]
    for f in utility_scripts:
        if os.path.exists(f):
            print(f"Moving {f} to scripts/utils/")
            shutil.move(f, os.path.join(SCRIPTS_UTILS, f))

    # 5. Reports and Text files
    txt_files = glob.glob("*.txt")
    for f in txt_files:
        print(f"Moving {f} to docs/reports/")
        shutil.move(f, os.path.join(DOCS_REPORTS, f))
    
    # 6. HTML outputs
    for f in ["product_test.html", "reporte_hunterprice.html"]:
        if os.path.exists(f):
            print(f"Moving {f} to docs/reports/")
            shutil.move(f, os.path.join(DOCS_REPORTS, f))

    # 7. React Bits (External)
    if os.path.exists("react-bits") and os.path.isdir("react-bits"):
        print("Moving react-bits to external/")
        # shutil.move doesn't work well for non-empty dirs across drives but here it should be fine
        shutil.move("react-bits", os.path.join(EXTERNAL, "react-bits"))

def delete_trash():
    # Broken directories
    trash_dirs = ["cUsersFacunOneDriveEscritorioPROYECTOS", "PERSONALESPRECIOStargetsyaguar"]
    for d in trash_dirs:
        if os.path.exists(d):
            print(f"Deleting trash directory: {d}")
            shutil.rmtree(d, ignore_errors=True)
    
    # Large temporary JSONs in root (keeping output_yaguar.json as ref if needed)
    if os.path.exists("data_hunterprice.json"):
        print("Moving data_hunterprice.json to archive/")
        shutil.move("data_hunterprice.json", os.path.join(ARCHIVE, "data_hunterprice.json"))

if __name__ == "__main__":
    make_dirs()
    move_files()
    delete_trash()
    print("\n✅ CLEANUP COMPLETE.")

import json

def xray_json():
    try:
        with open("turismocity_success.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        print(f"📦 Tipo de dato raíz: {type(data)}")
        
        if isinstance(data, dict):
            print(f"🔑 Claves raíz: {list(data.keys())}")
            # Profundizar en claves sospechosas
            for key in ["flights", "itineraries", "data", "results"]:
                if key in data:
                    val = data[key]
                    print(f"   ➡️ Clave '{key}': {type(val)} con len={len(val) if hasattr(val, '__len__') else 'N/A'}")
                    if isinstance(val, list) and len(val) > 0:
                         print(f"      Ejemplo item 0 keys: {list(val[0].keys()) if isinstance(val[0], dict) else 'No dict'}")

        elif isinstance(data, list):
            print(f"📏 Longitud de lista: {len(data)}")
            if len(data) > 0:
                print(f"   ➡️ Item 0 type: {type(data[0])}")
                if isinstance(data[0], dict):
                    print(f"   🔑 Item 0 keys: {list(data[0].keys())}")
                    
    except Exception as e:
        print(f"💥 Error: {e}")

if __name__ == "__main__":
    xray_json()

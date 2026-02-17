import json
import re

def fix_json_file():
    input_file = "turismocity_success.json"
    output_file = "turismocity_clean.json"
    
    try:
        with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            
        print(f"📦 Archivo original leído: {len(content)} caracteres.")
        
        # Buscar el primer '{' o '['
        start_brace = content.find('{')
        start_bracket = content.find('[')
        
        start_index = -1
        if start_brace != -1 and (start_bracket == -1 or start_brace < start_bracket):
            start_index = start_brace
            print(f"🔍 Detectado inicio de OBJETO JSON ('{{') en posición {start_index}")
        elif start_bracket != -1:
            start_index = start_bracket
            print(f"🔍 Detectado inicio de MATRIZ JSON ('[') en posición {start_index}")
            
        if start_index == -1:
            print("❌ No se encontró estructura JSON válida en el archivo.")
            return

        json_content = content[start_index:]
        
        # Intentar parsear para validar
        try:
            data = json.loads(json_content)
            print("✅ JSON validado correctamente.")
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"💾 Guardado limpio en: {output_file}")
            
        except json.JSONDecodeError as e:
            print(f"⚠️ El JSON extraído aún tiene errores: {e}")
            # Intento de fuerza bruta: cortar hasta el último '}' o ']'
            last_brace = json_content.rfind('}')
            last_bracket = json_content.rfind(']')
            end_index = max(last_brace, last_bracket) + 1
            
            json_content = json_content[:end_index]
            try:
                data = json.loads(json_content)
                print("✅ JSON validado tras recorte final.")
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            except:
                print("❌ Imposible reparar automáticamente.")

    except Exception as e:
        print(f"💥 Error al procesar archivo: {e}")

if __name__ == "__main__":
    fix_json_file()

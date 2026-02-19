import pandas as pd
import numpy as np
from rapidfuzz import process, fuzz
import warnings

# Configuración y Constantes
FILE_PATH = 'Precios competidores.xlsx'
OUTPUT_HTML = 'reporte_hunterprice.html'
OUTPUT_JSON = 'data_hunterprice.json'

# Mapeo de columnas a mantener (si existen) y normalizar
COLUMNAS_COMPETENCIA = [
    'CARREFOUR', 'COTO', 'DIARCO', 'MAKRO', 'MAXICONSUMO', 
    'NINI', 'PLAZA VEA', 'VITAL', 'YAGUAR', 'MAYORISTA Y', 'MAYORISTA X' # Agrega más si aparecen
]

def cargar_datos(file_path):
    print(f"🚀 Iniciando HunterPrice Engine v1.0...")
    print(f"📂 Leyendo archivo maestro: {file_path}")
    
    try:
        # Leemos detectando el encabezado en la fila 4 (0-indexed es 4)
        df = pd.read_excel(file_path, sheet_name='Hoja1', header=4)
        
        # Normalización básica de columnas
        df.columns = [str(col).strip() for col in df.columns]
        print(f"📋 Columnas encontradas: {df.columns.tolist()}")

        # Identificar columna de Descripción
        col_desc = next((col for col in df.columns if 'descripci' in col.lower()), None)
        if col_desc:
            print(f"✅ Columna de descripción detectada: '{col_desc}'")
            df.rename(columns={col_desc: 'Descripción'}, inplace=True)
        else:
            print("❌ ALERTA: No se encontró columna de Descripción exacta.")

        
        # Identificar columnas de competidores presentes
        competidores_encontrados = [col for col in df.columns if col in COLUMNAS_COMPETENCIA or col.upper() in COLUMNAS_COMPETENCIA]
        
        print(f"✅ Competidores detectados: {competidores_encontrados}")
        
        return df, competidores_encontrados
    
    except Exception as e:
        print(f"❌ Error crítico cargando archivo: {e}")
        return None, []

def limpiar_datos(df, competidores):
    print("🧹 Ejecutando Pipeline de Limpieza Profunda...")
    
    # 1. Eliminar filas vacías clave
    df = df.dropna(subset=['Material', 'Descripción'])
    
    # 2. Integridad de Material (SKU)
    df['Material'] = df['Material'].astype(str).str.replace(r'\.0$', '', regex=True)
    
    # 3. Normalización de Texto
    df['Descripcion_Norm'] = df['Descripción'].astype(str).str.upper().str.strip()
    
    # Reemplazos comunes de unidades
    reemplazos = {
        '1.5 L': ' 1.5L ', '1.5L': ' 1.5L ', '1500 ML': ' 1.5L ', '1500ML': ' 1.5L ',
        'CC': ' ML ', 'GRS': ' GR ', 'X 1 U': ''
    }
    for k, v in reemplazos.items():
        df['Descripcion_Norm'] = df['Descripcion_Norm'].str.replace(k, v)
        
    df['Descripcion_Norm'] = df['Descripcion_Norm'].str.replace(r'\s+', ' ', regex=True).str.strip()
    
    return df

    return df

def unificar_nombres_fuzzy(df):
    print("🤖 Ejecutando Unificación Semántica (Auto-Clustering)...")
    # Crear una columna para el nombre unificado
    df['Nombre_Unificado'] = df['Descripcion_Norm'].copy()
    
    # Obtener nombres únicos y ordenarlos por longitud (los más cortos suelen ser más genéricos/correctos para agrupar)
    unique_names = sorted(df['Descripcion_Norm'].unique(), key=len)
    
    # Diccionario de mapeo
    mapping = {name: name for name in unique_names}
    
    # Optimización: Solo comparamos si tienen palabras clave compartidas o longitudes similares
    # Esto es una simplificación para velocidad. En producción usaríamos grafos.
    # Por ahora, usamos una pasada simple de corrección.
    # "COCA COLA 1.5" -> "COCA COLA 1.5L"
    
    # Exportamos los sospechosos a un CSV aparte para revisión humana (Socio)
    duplicados_detectados = []
    
    # (Lógica simplificada para esta versión V1: solo notificamos, no alteramos destructivamente sin revisión)
    # Pero sí limpiamos "ruido" extra
    df['Nombre_Unificado'] = df['Nombre_Unificado'].str.replace(r'X\s*\d+\s*[Uu]', '', regex=True).str.strip()
    
    print("✅ Nombres normalizados para agrupación.")
    return df

def generar_archivos_finales(df):
    print("💾 Generando Bases de Datos (JSON + CSV)...")
    # JSON para el dashboard web futuro
    df.to_json(OUTPUT_JSON, orient='records', force_ascii=False)
    
    # CSV para Excel
    df.to_csv('HunterPrice_Master_Data.csv', index=False, decimal=',')

def generar_html_premium(df, competidores_cols):
    print("🎨 Generando Dashboard Interactivo Premium V2 (Professional Market Intelligence)...")
    
    df_html = df[df['Ahorro_Pct'] > 0].copy()
    
    # Preparamos los datos incluyendo los precios individuales de cada competidor para la tabla detalle
    # Rellenamos NaN con 0 o -1 para manejarlo en JS
    df_html_export = df_html.copy()
    df_html_export = df_html_export.fillna(0)
    
    # Columnas a exportar: Metadata + Competidores
    cols_export = ['Descripcion_Norm', 'Precio_Minimo', 'Precio_Promedio', 'Ganador', 'Ahorro_Pct', 'Ahorro_Abs'] + competidores_cols
    
    data_js = df_html_export[cols_export].to_dict(orient='records')
    import json
    json_data = json.dumps(data_js)
    competidores_json = json.dumps(competidores_cols)
    
    html_template = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HunterPrice AI | Market Intelligence</title>
    <!-- Fuente Inter para look profesional -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-body: #0f172a;
            --bg-card: #1e293b;
            --bg-header: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-primary: #3b82f6; /* Blue 500 */
            --accent-success: #22c55e; /* Green 500 */
            --accent-warning: #eab308; /* Yellow 500 */
            --border-color: #334155;
        }}
        
        * {{ box-sizing: border-box; }}
        
        body {{ 
            font-family: 'Inter', sans-serif; 
            background-color: var(--bg-body); 
            color: var(--text-main); 
            margin: 0; 
            padding-bottom: 50px;
        }}

        /* Header Profesional */
        .navbar {{
            background-color: var(--bg-header);
            border-bottom: 1px solid var(--border-color);
            padding: 15px 20px;
            position: sticky;
            top: 0;
            z-index: 100;
            display: flex;
            justify-content: center;
            align-items: center;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        }}
        
        .brand {{ 
            font-weight: 800; 
            font-size: 1.5rem; 
            letter-spacing: -0.05em;
            background: linear-gradient(to right, #60a5fa, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        /* Contenedor Principal */
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}

        /* Buscador */
        .search-wrapper {{
            margin: 30px 0;
            position: relative;
        }}
        .search-input {{
            width: 100%;
            padding: 16px 24px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            color: white;
            font-size: 1.1rem;
            transition: all 0.2s;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        .search-input:focus {{
            outline: none;
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
        }}

        /* Grid de Resultados */
        .results-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }}

        /* Tarjeta de Producto */
        .product-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            overflow: hidden;
            transition: transform 0.2s, box-shadow 0.2s;
            display: flex;
            flex-direction: column;
        }}
        .product-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
            border-color: var(--text-muted);
        }}

        .card-header {{
            padding: 20px;
            border-bottom: 1px solid var(--border-color);
        }}

        .product-title {{
            font-size: 1.1rem;
            font-weight: 600;
            line-height: 1.4;
            color: var(--text-main);
            margin-bottom: 10px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            height: 3.1em;
        }}

        .badges {{ display: flex; gap: 8px; flex-wrap: wrap; }}
        
        .badge {{
            font-size: 0.75rem;
            padding: 4px 10px;
            border-radius: 9999px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .badge-winner {{ background: rgba(34, 197, 94, 0.15); color: var(--accent-success); border: 1px solid rgba(34, 197, 94, 0.3); }}
        .badge-saving {{ background: rgba(234, 179, 8, 0.15); color: var(--accent-warning); border: 1px solid rgba(234, 179, 8, 0.3); }}

        .card-body {{
            padding: 20px;
            flex-grow: 1;
        }}

        .price-section {{
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            margin-bottom: 20px;
        }}
        
        .main-price {{ font-size: 2rem; font-weight: 800; color: white; letter-spacing: -1px; line-height: 1; }}
        .main-price small {{ font-size: 0.9rem; font-weight: 400; color: var(--text-muted); display: block; margin-top: 5px; }}
        
        .avg-price {{ text-align: right; }}
        .avg-label {{ font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; }}
        .avg-value {{ font-size: 1.1rem; color: var(--text-muted); text-decoration: line-through; }}

        /* Tabla Comparativa Desplegable */
        .market-table-container {{
            background: #0f172a;
            margin: 0 -20px -20px -20px;
            padding: 0;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
            border-top: 1px solid var(--border-color);
        }}
        
        .product-card.active .market-table-container {{
            max-height: 500px; /* Suficiente para mostrar competidores */
            overflow-y: auto;
        }}

        .market-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
        }}
        
        .market-table th, .market-table td {{
            padding: 10px 20px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}
        
        .market-table th {{ color: var(--text-muted); font-weight: 600; background: #162032; position: sticky; top: 0; }}
        .market-table td {{ color: var(--text-main); }}
        
        .toggle-btn {{
            background: transparent;
            border: none;
            width: 100%;
            padding: 12px;
            color: var(--accent-primary);
            font-weight: 600;
            cursor: pointer;
            border-top: 1px solid var(--border-color);
            transition: background 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }}
        .toggle-btn:hover {{ background: rgba(59, 130, 246, 0.1); }}

        /* Utilidades */
        .text-success {{ color: var(--accent-success); }}
        .text-danger {{ color: var(--danger); }}
        .hidden {{ display: none; }}

    </style>
</head>
<body>

    <nav class="navbar">
        <div class="brand">HunterPrice AI</div>
    </nav>

    <div class="container">
        
        <div class="search-wrapper">
            <input type="text" id="searchInput" class="search-input" placeholder="🔍 Buscar producto, marca o código..." onkeyup="filterProducts()">
        </div>

        <div id="stats" style="margin-bottom: 20px; color: var(--text-muted); font-size: 0.9rem;">
            Mostrando <span id="count" style="color: white; font-weight: bold;">0</span> oportunidades de mercado.
        </div>

        <div class="results-grid" id="productGrid">
            <!-- JS Injection -->
        </div>
    </div>

    <script>
        const products = {json_data};
        const competitors = {competidores_json};

        // Formateador de moneda
        const fmtMoney = (amount) => {{
            if (!amount || amount <= 0) return '-';
            return new Intl.NumberFormat('es-AR', {{ style: 'currency', currency: 'ARS', maximumFractionDigits: 0 }}).format(amount);
        }};

        function renderProducts(data) {{
            const grid = document.getElementById('productGrid');
            grid.innerHTML = '';
            document.getElementById('count').innerText = data.length;

            // Renderizar máximo 100 para no saturar DOM en móvil, scroll infinito sería ideal para V2
            const displayData = data.slice(0, 100);

            displayData.forEach((p, index) => {{
                const card = document.createElement('div');
                card.className = 'product-card';
                card.id = `card-${{index}}`;

                // Generar filas de tabla
                let tableRows = '';
                competitors.forEach(comp => {{
                    const price = p[comp];
                    const isWinner = price === p.Precio_Minimo && price > 0;
                    const rowClass = isWinner ? 'background: rgba(34, 197, 94, 0.1);' : '';
                    const priceClass = isWinner ? 'color: var(--accent-success); font-weight: bold;' : '';
                    
                    if (price > 0) {{ // Solo mostrar si tiene precio
                        tableRows += `
                            <tr style="${{rowClass}}">
                                <td>${{comp}}</td>
                                <td style="${{priceClass}} text-align: right;">${{fmtMoney(price)}}</td>
                            </tr>
                        `;
                    }}
                }});

                card.innerHTML = `
                    <div class="card-header">
                        <div class="product-title">${{p.Descripcion_Norm}}</div>
                        <div class="badges">
                            <span class="badge badge-winner">🏆 ${{p.Ganador}}</span>
                            <span class="badge badge-saving">📉 -${{p.Ahorro_Pct.toFixed(0)}}%</span>
                        </div>
                    </div>
                    
                    <div class="card-body">
                        <div class="price-section">
                            <div class="main-price">
                                ${{fmtMoney(p.Precio_Minimo)}}
                                <small>Mejor Precio Detectado</small>
                            </div>
                            <div class="avg-price">
                                <div class="avg-label">Promedio Mercado</div>
                                <div class="avg-value">${{fmtMoney(p.Precio_Promedio)}}</div>
                            </div>
                        </div>
                    </div>

                    <button class="toggle-btn" onclick="toggleDetails(${{index}})">
                        📊 Ver Comparativa de Mercado Completa
                    </button>

                    <div class="market-table-container">
                        <table class="market-table">
                            <thead>
                                <tr>
                                    <th>Competidor</th>
                                    <th style="text-align: right;">Precio Lista</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${{tableRows}}
                            </tbody>
                        </table>
                    </div>
                `;
                grid.appendChild(card);
            }});
        }}

        function toggleDetails(index) {{
            const card = document.getElementById(`card-${{index}}`);
            card.classList.toggle('active');
            const btn = card.querySelector('.toggle-btn');
            if (card.classList.contains('active')) {{
                btn.innerHTML = '🔼 Ocultar Detalle';
                btn.style.borderTopColor = 'transparent';
            }} else {{
                btn.innerHTML = '📊 Ver Comparativa de Mercado Completa';
                btn.style.borderTopColor = '#334155';
            }}
        }}

        function filterProducts() {{
            const query = document.getElementById('searchInput').value.toLowerCase();
            const filtered = products.filter(p => 
                p.Descripcion_Norm.toLowerCase().includes(query) || 
                p.Ganador.toLowerCase().includes(query)
            );
            renderProducts(filtered);
        }}

        // Inicializar
        renderProducts(products);
    </script>
</body>
</html>
    """
    
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"✅ Dashboard HTML Premium V2 generado exitosamente: {OUTPUT_HTML}")


def analizar_mercado(df, competidores):
    print("🧠 Ejecutando Análisis de Inteligencia de Mercado...")
    
    df = df.copy() # Evitar SettingWithCopyWarning
    
    # Convertir precios a numérico (forzando errores a NaN)
    for col in competidores:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Calcular métricas por fila
    df['Precio_Minimo'] = df[competidores].min(axis=1)
    df['Precio_Maximo'] = df[competidores].max(axis=1)
    df['Precio_Promedio'] = df[competidores].mean(axis=1)
    df['Competidores_Activos'] = df[competidores].count(axis=1)
    
    # Identificar al ganador (quién tiene el mínimo)
    def encontrar_ganador(row):
        min_val = row['Precio_Minimo']
        if pd.isna(min_val):
            return "N/A"
        ganadores = [comp for comp in competidores if row[comp] == min_val]
        return ", ".join(ganadores)

    df['Ganador'] = df.apply(encontrar_ganador, axis=1)
    
    # Calcular Ahorro Potencial (vs Promedio)
    df['Ahorro_Pct'] = ((df['Precio_Promedio'] - df['Precio_Minimo']) / df['Precio_Promedio']) * 100
    df['Ahorro_Abs'] = df['Precio_Promedio'] - df['Precio_Minimo']
    
    return df

    return df

def generar_reporte_consola(df):
    print("\n" + "="*50)
    print("       📊 REPORTE PRELIMINAR HUNTERPRICE       ")
    print("="*50)
    
    # Filtramos casos donde el Ahorro sea NaN o negativo por errores de data
    df_valid = df[df['Ahorro_Pct'] > 0]
    
    top_ahorros = df_valid.sort_values(by='Ahorro_Pct', ascending=False).head(10)
    
    print("\n🔥 TOP 10 OPORTUNIDADES DE AHORRO (Arbitraje/Flipping):")
    for idx, row in top_ahorros.iterrows():
        print(f"- {row['Descripcion_Norm'][:40]}...")
        print(f"  💰 Mínimo: ${row['Precio_Minimo']:,.2f} en [{row['Ganador']}]")
        print(f"  📈 Promedio: ${row['Precio_Promedio']:,.2f} | 📉 Ahorro: {row['Ahorro_Pct']:.1f}%")
        print("-" * 30)

    # Detección rápida de inconsistencias
    posibles_errores = df[df['Ahorro_Pct'] > 60]
    if not posibles_errores.empty:
        print(f"\n⚠️ ALERTA: {len(posibles_errores)} productos con dispersión > 60% (Posible Error o Flipping Brutal)")

def main():
    df, competidores = cargar_datos(FILE_PATH)
    if df is not None:
        if not competidores:
            print("⚠️ No se detectaron columnas de competidores estándar. Revisando cabeceras...")
        else:
            df = limpiar_datos(df, competidores)
            df = unificar_nombres_fuzzy(df)
            df = analizar_mercado(df, competidores)
            
            generar_reporte_consola(df)
            generar_archivos_finales(df)
            generar_html_premium(df, competidores)
            
            print("\n✅ CICLO COMPLETO FINALIZADO.")

if __name__ == "__main__":
    main()

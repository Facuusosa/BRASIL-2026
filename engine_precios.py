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
    print(f"🚀 Iniciando HunterPrice Engine v3.0 (Vertical SAP Mode)...")
    print(f"📂 Leyendo archivo maestro: {file_path}")
    
    try:
        xls = pd.ExcelFile(file_path)
        sheet_name = 'SAP Document Export' if 'SAP Document Export' in xls.sheet_names else xls.sheet_names[0]
        df_raw = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # Normalización de columnas de SAP
        col_mapping = {
            'COMPETIDOR': 'Competidor',
            'Material': 'Material',
            'Descripción de Material': 'Descripción',
            'Tipo de lista de precios': 'Tipo',
            'Descripción Grupo Articulo': 'Rubro',
            'Precio': 'Precio'
        }
        df_raw.rename(columns=col_mapping, inplace=True)
        
        print(f"✅ Filas crudas procesadas: {len(df_raw)}")
        return df_raw
    
    except Exception as e:
        print(f"❌ Error crítico cargando archivo: {e}")
        return None

def limpiar_y_pivotar(df):
    print("🧹 Ejecutando Pipeline de Limpieza y Pivotado Vertical...")
    
    # 1. Limpieza básica
    df = df.dropna(subset=['Material', 'Descripción', 'Precio']).copy()
    df['Material'] = df['Material'].astype(str).str.replace(r'\.0$', '', regex=True)
    df['Descripcion_Norm'] = df['Descripción'].astype(str).str.upper().str.strip()
    
    # 2. Normalización de Rubros: Para un mismo material, nos quedamos con el rubro que más se repite
    print("🔖 Normalizando categorías (Rubros)...")
    rubro_master = df.groupby('Material')['Rubro'].agg(lambda x: x.mode()[0] if not x.mode().empty else "S/D").to_dict()
    df['Rubro'] = df['Material'].map(rubro_master)

    # 3. Manejo de duplicados (Mismos precios para mismo competidor/material)
    # Si hay Oferta y Lista, nos quedamos con el mejor precio por cada competidor para ese producto
    idx_min = df.groupby(['Material', 'Competidor'])['Precio'].idxmin()
    df_min = df.loc[idx_min].copy()
    
    # 4. Pivotado: Productos en filas, Competidores en columnas
    print("🔄 Transformando datos verticales a matriz de mercado...")
    # Agregamos la descripción a la agrupación para mantenerla tras el pivot
    # Si hay descripciones distintas para un mismo material, tomamos la más larga (suele ser la más completa)
    desc_master = df_min.groupby('Material')['Descripcion_Norm'].agg(lambda x: sorted(list(x), key=len, reverse=True)[0]).to_dict()
    
    df_pivot = df_min.pivot(index='Material', 
                            columns='Competidor', 
                            values='Precio')
    
    # Restaurar Metadata
    df_pivot = df_pivot.reset_index()
    df_pivot['Descripcion_Norm'] = df_pivot['Material'].map(desc_master)
    df_pivot['Rubro'] = df_pivot['Material'].map(rubro_master)
    
    # Reordenar columnas para que Metadata esté al principio
    cols = ['Material', 'Descripcion_Norm', 'Rubro']
    competidores = [c for c in df_pivot.columns if c not in cols]
    df_pivot = df_pivot[cols + competidores]
    
    # Crear un mapeo de 'Material' -> {'Competidor': 'Tipo'} para saber si el precio es OFERTA
    print("🏷️ Mapeando tipos de precios (Oferta/Lista)...")
    tipo_mapping = df_min.set_index(['Material', 'Competidor'])['Tipo'].to_dict()
    
    return df_pivot, competidores, tipo_mapping
def extraer_unidad(nombre):
    """Extrae cantidad y unidad (ml, gr, kg, etc.) de la descripción."""
    import re
    # Patrón para capturar número + unidad (ej: 500ML, 1.5 LT, 900 GR)
    match = re.search(r'(\d+[\.,]?\d*)\s*(ML|CC|LT|L|GR|KG|G|K|U|UN)', nombre, re.IGNORECASE)
    if match:
        valor = match.group(1).replace(',', '.')
        unidad = match.group(2).upper()
        # Normalizar unidades
        if unidad in ['LT', 'L']: valor = float(valor) * 1000; unidad = 'ML'
        if unidad in ['KG', 'K']: valor = float(valor) * 1000; unidad = 'GR'
        if unidad in ['CC']: unidad = 'ML'
        if unidad in ['G']: unidad = 'GR'
        return f"{int(float(valor))}{unidad}"
    return "S/U"

def unificar_nombres_fuzzy(df):
    print("🤖 Ejecutando Unificación Semántica (Capa de Inteligencia)...")
    
    # 1. Normalización de Unidades para evitar falsos positivos
    df['Unidad_Metrica'] = df['Descripcion_Norm'].apply(extraer_unidad)
    
    # 2. Generar un 'Boceto de Marca' simple (primera palabra de la descripción)
    df['Marca_Sugerida'] = df['Descripcion_Norm'].str.split().str[0]
    
    # NOTA: En un entorno de producción real aquí usaríamos clustering (DBScan) 
    # o un clasificador de lenguaje natural. 
    # Por ahora, aseguramos que la Descripcion_Norm esté limpia de basura común.
    
    df['Nombre_Unificado'] = df['Descripcion_Norm'].str.replace(r'X\s*\d+\s*[Uu]', '', regex=True).str.strip()
    
    print("✅ Inteligencia semántica aplicada.")
    return df

def generar_archivos_finales(df):
    print("💾 Generando Bases de Datos (JSON + CSV)...")
    # JSON para el dashboard web futuro
    df.to_json(OUTPUT_JSON, orient='records', force_ascii=False)
    
    # CSV para Excel
    df.to_csv('HunterPrice_Master_Data.csv', index=False, decimal=',')

def generar_html_premium(df, competidores_cols):
    print("🎨 Generando Dashboard Interactivo Premium V3 (Professional Market Intelligence)...")
    
    # Filtrar solo productos con precio (evitar filas vacías)
    df_html = df[df['Precio_Minimo'] > 0].copy()
    
    # Estadísticas para el "Resumen de Impacto"
    total_articulos = len(df_html)
    ahorro_total_estimado = df_html['Ahorro_Abs'].sum()
    promedio_ahorro_pct = df_html['Ahorro_Pct'].mean()
    bombas_detectadas = df_html['Es_Bomba'].sum()
    
    # Preparamos los datos
    df_html_export = df_html.fillna(0)
    
    # Columnas a exportar
    cols_export = [
        'Material', 'Descripcion_Norm', 'Rubro', 'Precio_Minimo', 
        'Precio_Promedio', 'Ganador', 'Ahorro_Pct', 'Ahorro_Abs', 
        'Tipo_Ganador', 'Es_Bomba', 'Unidad_Metrica', 'Marca_Sugerida'
    ] + competidores_cols
    
    data_js = df_html_export[cols_export].to_dict(orient='records')
    import json
    json_data = json.dumps(data_js)
    competidores_json = json.dumps(competidores_cols)
    rubros_json = json.dumps(sorted(df_html_export['Rubro'].unique().tolist()))
    
    html_template = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HunterPrice AI | Intelligence Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/lucide@0.344.0/dist/umd/lucide.min.js"></script>
    <style>
        :root {{
            --bg: #05070a;
            --surface: #0f1218;
            --surface-accent: #171c26;
            --accent: #3b82f6;
            --accent-glow: rgba(59, 130, 246, 0.3);
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --bomba: #ff4700;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border: rgba(255,255,255,0.08);
            --glass: rgba(15, 18, 24, 0.8);
        }}
        
        * {{ box-sizing: border-box; font-family: 'Outfit', sans-serif; -webkit-tap-highlight-color: transparent; }}
        body {{ background-color: var(--bg); color: var(--text-main); margin: 0; min-height: 100vh; line-height: 1.5; }}

        /* Glassmorphism Header */
        .header {{ 
            background: var(--glass);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            padding: 1rem 2rem; 
            border-bottom: 1px solid var(--border);
            display: flex; justify-content: space-between; align-items: center;
            position: sticky; top: 0; z-index: 1000;
        }}
        .brand {{ display: flex; align-items: center; gap: 0.75rem; font-weight: 800; font-size: 1.5rem; letter-spacing: -0.02em; }}
        .brand span {{ color: var(--accent); }}
        .header-meta {{ font-size: 0.85rem; color: var(--text-muted); display: flex; gap: 1.5rem; }}

        .container {{ padding: 2rem; max-width: 1400px; margin: 0 auto; }}

        /* KPI Grid */
        .kpi-grid {{ 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); 
            gap: 1.5rem; margin-bottom: 2.5rem; 
        }}
        .kpi-card {{ 
            background: var(--surface); border: 1px solid var(--border); 
            padding: 1.5rem; border-radius: 16px; position: relative; overflow: hidden;
            transition: transform 0.3s ease;
        }}
        .kpi-card:hover {{ transform: translateY(-4px); border-color: var(--accent); }}
        .kpi-label {{ color: var(--text-muted); font-size: 0.8rem; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em; }}
        .kpi-value {{ font-size: 1.8rem; font-weight: 800; margin-top: 0.5rem; display: flex; align-items: baseline; gap: 0.5rem; }}
        .kpi-sub {{ font-size: 0.85rem; color: var(--success); font-weight: 500; }}
        .kpi-card i {{ position: absolute; right: 1rem; top: 1rem; opacity: 0.1; transform: scale(2.5); }}

        /* Filters */
        .controls {{ 
            background: var(--surface); padding: 1.25rem; border-radius: 16px; 
            border: 1px solid var(--border); margin-bottom: 2rem;
            display: flex; gap: 1rem; flex-wrap: wrap; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        .search-wrapper {{ flex: 1; min-width: 300px; position: relative; }}
        .search-wrapper i {{ position: absolute; left: 1rem; top: 50%; transform: translateY(-50%); color: var(--text-muted); }}
        input, select {{
            width: 100%; background: #05070a; border: 1px solid var(--border);
            color: white; padding: 0.75rem 1rem 0.75rem 2.75rem; border-radius: 10px; 
            font-size: 0.95rem; transition: all 0.2s ease;
        }}
        select {{ padding-left: 1rem; cursor: pointer; }}
        input:focus, select:focus {{ outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow); }}

        /* Quick Filters */
        .quick-filters {{ display: flex; gap: 0.75rem; }}
        .btn-filter {{
            background: var(--surface-accent); border: 1px solid var(--border);
            color: var(--text-main); padding: 0.75rem 1.25rem; border-radius: 10px;
            cursor: pointer; font-weight: 600; display: flex; align-items: center; gap: 0.5rem;
            transition: all 0.2s ease;
        }}
        .btn-filter.active {{ background: var(--accent); border-color: transparent; }}
        .btn-filter.bomba {{ border-color: var(--bomba); color: var(--bomba); }}
        .btn-filter.bomba.active {{ background: var(--bomba); color: white; }}

        /* Table Design */
        .table-container {{ 
            background: var(--surface); border-radius: 20px; border: 1px solid var(--border);
            overflow: hidden; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.4);
        }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; }}
        thead {{ background: var(--surface-accent); }}
        th {{ 
            padding: 1rem 1.5rem; font-size: 0.75rem; color: var(--text-muted); 
            text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; 
        }}
        td {{ padding: 1.25rem 1.5rem; border-bottom: 1px solid var(--border); vertical-align: middle; }}
        tr:last-child td {{ border-bottom: none; }}
        tr.row-main {{ cursor: pointer; transition: background 0.2s; }}
        tr.row-main:hover {{ background: rgba(255,255,255,0.02); }}

        /* Product Cells */
        .product-info .title {{ font-weight: 700; font-size: 0.95rem; color: #fff; margin-bottom: 0.25rem; }}
        .product-info .meta {{ display: flex; gap: 0.5rem; font-size: 0.7rem; color: var(--text-muted); }}
        .tag {{ background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 4px; }}
        
        .price-cell {{ font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 1.1rem; }}
        .saving-badge {{ 
            background: rgba(16, 185, 129, 0.15); color: var(--success); 
            padding: 4px 8px; border-radius: 6px; font-weight: 800; font-size: 0.8rem;
        }}
        
        /* Bomba Badge */
        .badge-bomba {{
            background: rgba(255, 71, 0, 0.15); color: var(--bomba);
            border: 1px solid var(--bomba); padding: 4px 10px; border-radius: 99px;
            font-size: 0.65rem; font-weight: 800; text-transform: uppercase;
            display: inline-flex; align-items: center; gap: 4px;
            animation: pulse-bomba 2s infinite;
        }}
        @keyframes pulse-bomba {{
            0% {{ box-shadow: 0 0 0 0 rgba(255, 71, 0, 0.4); }}
            70% {{ box-shadow: 0 0 0 10px rgba(255, 71, 0, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(255, 71, 0, 0); }}
        }}

        /* Detail Row Matrix */
        .row-detail {{ display: none; background: #05070a; }}
        .row-detail.active {{ display: table-row; }}
        .matrix-grid {{ 
            display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); 
            gap: 1rem; padding: 2rem; animation: slideIn 0.3s ease-out;
        }}
        @keyframes slideIn {{ from {{ opacity:0; transform: translateY(-10px); }} to {{ opacity:1; transform: translateY(0); }} }}
        
        .matrix-item {{ 
            background: var(--surface-accent); padding: 1rem; border-radius: 12px; 
            border: 1px solid var(--border); display: flex; flex-direction: column;
        }}
        .matrix-item.is-winner {{ border-color: var(--success); background: rgba(16, 185, 129, 0.05); }}
        .matrix-name {{ font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; font-weight: 600; }}
        .matrix-price {{ font-size: 1.1rem; font-weight: 700; margin-top: 0.25rem; font-family: 'JetBrains Mono', monospace; }}

        /* Mobile Optimization */
        @media (max-width: 900px) {{
            .header-meta, th:nth-child(2), td:nth-child(2), th:nth-child(5), td:nth-child(5) {{ display: none; }}
            .kpi-grid {{ grid-template-columns: 1fr 1fr; }}
            .container {{ padding: 1rem; }}
        }}
    </style>
</head>
<body>

    <header class="header">
        <div class="brand">
            <i data-lucide="zap" fill="currentColor"></i>
            HunterPrice<span>AI</span>
        </div>
        <div class="header-meta">
            <div><i data-lucide="calendar"></i> 12 Mar 2026</div>
            <div><i data-lucide="activity"></i> V3.2 PRO</div>
        </div>
    </header>

    <div class="container">
        
        <!-- Dashboard Stats -->
        <div class="kpi-grid">
            <div class="kpi-card">
                <i data-lucide="package"></i>
                <div class="kpi-label">Productos Indexados</div>
                <div class="kpi-value">{total_articulos:,.0f}</div>
            </div>
            <div class="kpi-card">
                <i data-lucide="trending-down"></i>
                <div class="kpi-label">Ahorro Promedio</div>
                <div class="kpi-value">{promedio_ahorro_pct:.1f}%</div>
            </div>
            <div class="kpi-card">
                <i data-lucide="flame" style="color:var(--bomba)"></i>
                <div class="kpi-label">Bombas Detectadas</div>
                <div class="kpi-value" style="color:var(--bomba)">{bombas_detectadas}</div>
            </div>
            <div class="kpi-card">
                <i data-lucide="wallet"></i>
                <div class="kpi-label">Impacto Potencial</div>
                <div class="kpi-value">
                    ${ahorro_total_estimado/1e6:.1f}M
                    <div class="kpi-sub">ARS</div>
                </div>
            </div>
        </div>

        <!-- Filters Section -->
        <div class="controls">
            <div class="search-wrapper">
                <i data-lucide="search"></i>
                <input type="text" id="q" placeholder="Buscar por nombre, código o marca..." onkeyup="app.filter()">
            </div>
            <div style="min-width: 200px;">
                <select id="rubroFilter" onchange="app.filter()">
                    <option value="">Todas las Categorías</option>
                </select>
            </div>
            <div class="quick-filters">
                <button id="btnBomba" class="btn-filter bomba" onclick="app.toggleBomba()">
                    <i data-lucide="flame"></i> BOMBAS
                </button>
            </div>
        </div>

        <!-- Main Data Table -->
        <div class="table-container">
            <table id="mainTable">
                <thead>
                    <tr>
                        <th>Producto / SKU</th>
                        <th>Rubro</th>
                        <th>Winner (Min)</th>
                        <th>Ahorro vs Promedio</th>
                        <th>Tendencia</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                    <!-- JS Data Injection -->
                </tbody>
            </table>
        </div>
    </div>

    <script>
        const app = {{
            data: {json_data},
            rubros: {rubros_json},
            competitors: {competidores_json},
            onlyBomba: false,
            
            init() {{
                lucide.createIcons();
                this.populateRubros();
                this.render(this.data);
            }},

            populateRubros() {{
                const select = document.getElementById('rubroFilter');
                this.rubros.forEach(r => {{
                    const opt = document.createElement('option');
                    opt.value = opt.innerText = r;
                    select.appendChild(opt);
                }});
            }},

            fmt(n) {{
                return new Intl.NumberFormat('es-AR', {{ style: 'currency', currency: 'ARS', maximumFractionDigits: 0 }}).format(n);
            }},

            toggleBomba() {{
                this.onlyBomba = !this.onlyBomba;
                document.getElementById('btnBomba').classList.toggle('active');
                this.filter();
            }},

            render(list) {{
                const body = document.getElementById('tableBody');
                body.innerHTML = '';
                
                list.slice(0, 500).forEach((p, i) => {{
                    const tr = document.createElement('tr');
                    tr.className = 'row-main';
                    tr.onclick = () => this.toggle(i);
                    
                    const isBomba = p.Es_Bomba;
                    const bombaBadge = isBomba ? '<span class="badge-bomba"><i data-lucide="zap" size="10"></i> BOMBA</span>' : '';
                    const isOffer = p.Tipo_Ganador === 'OFERTA';
                    
                    tr.innerHTML = `
                        <td>
                            <div class="product-info">
                                <div class="title">${{p.Descripcion_Norm}}</div>
                                <div class="meta">
                                    <span class="tag">SKU: ${{p.Material}}</span>
                                    <span class="tag">${{p.Unidad_Metrica != 'S/U' ? p.Unidad_Metrica : ''}}</span>
                                    ${{bombaBadge}}
                                </div>
                            </div>
                        </td>
                        <td><span style="color:var(--text-muted); font-size: 0.85rem;">${{p.Rubro}}</span></td>
                        <td>
                            <div style="font-size: 0.7rem; color:var(--text-muted)">${{p.Ganador}}</div>
                            <div class="price-cell" style="color: ${{isOffer ? 'var(--warning)' : 'var(--success)'}}">
                                ${{this.fmt(p.Precio_Minimo)}}
                            </div>
                        </td>
                        <td>
                            <div class="saving-badge">-${{p.Ahorro_Pct.toFixed(1)}}%</div>
                        </td>
                        <td>
                            <div style="font-size: 0.8rem; color: var(--text-muted); font-family: 'JetBrains Mono';">
                                Avg: ${{this.fmt(p.Precio_Promedio)}}
                            </div>
                        </td>
                    `;

                    const detail = document.createElement('tr');
                    detail.className = 'row-detail';
                    detail.id = 'detail-' + i;
                    
                    let matrixHtml = '';
                    this.competitors.forEach(c => {{
                        if(p[c] > 0) {{
                            const win = p[c] === p.Precio_Minimo;
                            matrixHtml += `
                                <div class="matrix-item ${{win ? 'is-winner' : ''}}">
                                    <div class="matrix-name">${{c}}</div>
                                    <div class="matrix-price" style="${{win ? 'color:var(--success)' : ''}}">${{this.fmt(p[c])}}</div>
                                </div>
                            `;
                        }}
                    }});

                    detail.innerHTML = `<td colspan="5"><div class="matrix-grid">${{matrixHtml}}</div></td>`;
                    
                    body.appendChild(tr);
                    body.appendChild(detail);
                }});
                lucide.createIcons();
            }},

            toggle(i) {{
                const el = document.getElementById('detail-'+i);
                const isActive = el.classList.contains('active');
                // Close others
                document.querySelectorAll('.row-detail').forEach(d => d.classList.remove('active'));
                if(!isActive) el.classList.add('active');
            }},

            filter() {{
                const q = document.getElementById('q').value.toLowerCase();
                const r = document.getElementById('rubroFilter').value;
                
                const filtered = this.data.filter(p => {{
                    const matchQ = p.Descripcion_Norm.toLowerCase().includes(q) || p.Material.includes(q);
                    const matchR = r === "" || p.Rubro === r;
                    const matchBomba = !this.onlyBomba || p.Es_Bomba;
                    return matchQ && matchR && matchBomba;
                }});
                this.render(filtered);
            }}
        }};

        app.init();
    </script>
</body>
</html>
    """
    
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"✅ Dashboard HTML Premium V3.2 (Course Ready) generado: {OUTPUT_HTML}")


def analizar_mercado(df, competidores, tipo_mapping):
    print("🧠 Ejecutando Análisis de Inteligencia de Mercado...")
    
    df = df.copy() # Evitar SettingWithCopyWarning
    
    # Calcular métricas por fila
    df['Precio_Minimo'] = df[competidores].min(axis=1)
    df['Precio_Maximo'] = df[competidores].max(axis=1)
    df['Precio_Promedio'] = df[competidores].mean(axis=1)
    df['Competidores_Activos'] = df[competidores].count(axis=1)
    
    # Identificar al ganador (quién tiene el mínimo)
    def encontrar_ganador_y_tipo(row):
        min_val = row['Precio_Minimo']
        if pd.isna(min_val) or min_val == 0:
            return "N/A", "LISTA"
        
        # Encontrar competidores que tienen el precio mínimo
        ganadores = [comp for comp in competidores if row[comp] == min_val]
        ganador_principal = ganadores[0]
        
        # Buscar el tipo (OFERTA/LISTA) en el mapping
        material = row['Material']
        tipo = tipo_mapping.get((material, ganador_principal), "LISTA")
        
        return ", ".join(ganadores), tipo

    res = df.apply(encontrar_ganador_y_tipo, axis=1)
    df['Ganador'] = [r[0] for r in res]
    df['Tipo_Ganador'] = [r[1] for r in res]
    
    # Calcular Ahorro Potencial (vs Promedio)
    df['Ahorro_Pct'] = ((df['Precio_Promedio'] - df['Precio_Minimo']) / df['Precio_Promedio']) * 100
    df['Ahorro_Abs'] = df['Precio_Promedio'] - df['Precio_Minimo']
    
    # DETECCIÓN DE BOMBAS (Glitches/Oportunidades de Flipping)
    # Una "Bomba" es cuando el precio es más de un 25% más barato que el promedio Y hay al menos 3 competidores
    df['Es_Bomba'] = (df['Ahorro_Pct'] > 25) & (df['Competidores_Activos'] >= 3)
    
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
        tipo_str = f" [{row['Tipo_Ganador']}]" if row['Tipo_Ganador'] == "OFERTA" else ""
        print(f"- {row['Descripcion_Norm'][:40]}...")
        print(f"  💰 Mínimo: ${row['Precio_Minimo']:,.2f} en [{row['Ganador']}]{tipo_str}")
        print(f"  📈 Promedio: ${row['Precio_Promedio']:,.2f} | 📉 Ahorro: {row['Ahorro_Pct']:.1f}%")
        print("-" * 30)

def main():
    df_raw = cargar_datos(FILE_PATH)
    if df_raw is not None:
        # 1. Pipeline de Limpieza y Pivotado (SAP Mode)
        df_pivot, competidores, tipo_mapping = limpiar_y_pivotar(df_raw)
        
        if not competidores:
            print("⚠️ No se detectaron columnas de competidores. Revisando Excel...")
            return

        # 2. Capa de Inteligencia Semántica (Basado en Principio de Producto: Resolver el Pain de Datos Sucios)
        df_unified = unificar_nombres_fuzzy(df_pivot)
        
        # 3. Análisis de Mercado (Detección de Bombas y Ahorros)
        df_final = analizar_mercado(df_unified, competidores, tipo_mapping)
        
        # 4. Generación de Salidas (Dashboard Premium + Data)
        generar_reporte_consola(df_final)
        generar_archivos_finales(df_final)
        generar_html_premium(df_final, competidores)
        
        print("\n✅ CICLO COMPLETO FINALIZADO (V3.2 Intelligence Mode).")
        print(f"🔗 Abre {OUTPUT_HTML} para ver los resultados.")

if __name__ == "__main__":
    main()

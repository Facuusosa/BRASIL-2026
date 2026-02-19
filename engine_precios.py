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
    
    # 2. Manejo de duplicados (Mismos precios para mismo competidor/material)
    # Si hay Oferta y Lista, nos quedamos con el mejor precio por cada competidor para ese producto
    idx_min = df.groupby(['Material', 'Competidor'])['Precio'].idxmin()
    df_min = df.loc[idx_min].copy()
    
    # Marcamos si es oferta en una columna aparte antes de pivotar
    # Para saber después en el dashboard si el ganador tiene oferta
    
    # 3. Pivotado: Productos en filas, Competidores en columnas
    print("🔄 Transformando datos verticales a matriz de mercado...")
    df_pivot = df_min.pivot(index=['Material', 'Descripcion_Norm', 'Rubro'], 
                            columns='Competidor', 
                            values='Precio')
    
    # Reset index para volver a tener columnas de material/descripcion
    df_pivot = df_pivot.reset_index()
    
    # Obtener lista de competidores dinámicamente
    competidores = [c for c in df_pivot.columns if c not in ['Material', 'Descripcion_Norm', 'Rubro']]
    
    # Crear un mapeo de 'Material' -> {'Competidor': 'Tipo'} para saber si el precio es OFERTA
    print("🏷️ Mapeando tipos de precios (Oferta/Lista)...")
    tipo_mapping = df_min.set_index(['Material', 'Competidor'])['Tipo'].to_dict()
    
    return df_pivot, competidores, tipo_mapping

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
    cols_export = ['Material', 'Descripcion_Norm', 'Rubro', 'Precio_Minimo', 'Precio_Promedio', 'Ganador', 'Ahorro_Pct', 'Ahorro_Abs', 'Tipo_Ganador'] + competidores_cols
    
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
    <title>HunterPrice AI | Control Panel V3</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-body: #0a0f1d;
            --bg-card: #161e31;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #3b82f6;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --border: #2d3748;
        }}
        
        * {{ box-sizing: border-box; font-family: 'Inter', sans-serif; }}
        body {{ background-color: var(--bg-body); color: var(--text-main); margin: 0; }}

        .navbar {{ 
            background: #111827; 
            padding: 1rem 2rem; 
            border-bottom: 1px solid var(--border);
            display: flex; justify-content: space-between; align-items: center;
            position: sticky; top: 0; z-index: 1000;
        }}
        .brand {{ font-weight: 800; font-size: 1.25rem; color: var(--accent); }}
        .badge-count {{ background: var(--accent); padding: 2px 8px; border-radius: 6px; font-size: 0.8rem; }}

        .container {{ padding: 2rem; max-width: 1400px; margin: 0 auto; }}

        /* Filters Bar */
        .controls {{ 
            display: flex; gap: 1rem; margin-bottom: 2rem; flex-wrap: wrap;
            background: var(--bg-card); padding: 1rem; border-radius: 12px; border: 1px solid var(--border);
        }}
        .search-box {{ flex-grow: 1; min-width: 300px; position: relative; }}
        input, select {{
            width: 100%; background: #0f172a; border: 1px solid var(--border);
            color: white; padding: 12px 16px; border-radius: 8px; font-size: 0.95rem;
        }}
        input:focus {{ outline: none; border-color: var(--accent); }}

        /* Data Table */
        .table-container {{ 
            background: var(--bg-card); border-radius: 12px; border: 1px solid var(--border);
            overflow: hidden; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5);
        }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 0.9rem; }}
        th {{ background: #1f2937; padding: 14px 16px; color: var(--text-muted); font-weight: 600; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.05em; }}
        td {{ padding: 12px 16px; border-bottom: 1px solid var(--border); vertical-align: middle; }}
        tr:hover {{ background: rgba(255,255,255,0.03); }}

        .row-main {{ cursor: pointer; }}
        .row-detail {{ display: none; background: #0f172a; }}
        .row-detail.active {{ display: table-row; }}

        .price-best {{ color: var(--success); font-weight: 700; font-size: 1.1rem; }}
        .badge-pill {{ padding: 4px 8px; border-radius: 6px; font-size: 0.7rem; font-weight: 700; }}
        .bg-offer {{ background: rgba(245, 158, 11, 0.2); color: var(--warning); border: 1px solid var(--warning); }}
        .bg-saving {{ background: rgba(16, 185, 129, 0.2); color: var(--success); }}

        /* Detailed Matrix */
        .matrix-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 1rem; padding: 20px; }}
        .matrix-item {{ background: #1e293b; padding: 12px; border-radius: 8px; border: 1px solid var(--border); }}
        .matrix-label {{ font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px; }}
        .matrix-value {{ font-weight: 600; font-size: 0.95rem; }}
        .is-winner {{ border-color: var(--success); background: rgba(16, 185, 129, 0.05); }}

        @media (max-width: 768px) {{
            th:nth-child(3), td:nth-child(3), th:nth-child(5), td:nth-child(5) {{ display: none; }}
        }}
    </style>
</head>
<body>

<nav class="navbar">
    <div class="brand">HunterPrice <span style="color:white">AI Control Panel</span></div>
    <div class="badge-count">V3.0 Professional</div>
</nav>

<div class="container">
    <div class="controls">
        <div class="search-box">
            <input type="text" id="q" placeholder="🔍 Buscar producto, marca o rubro..." onkeyup="app.filter()">
        </div>
        <div style="width: 250px;">
            <select id="rubroFilter" onchange="app.filter()">
                <option value="">Todos los Rubros</option>
                <!-- JS Inject -->
            </select>
        </div>
    </div>

    <div class="table-container">
        <table id="mainTable">
            <thead>
                <tr>
                    <th>Producto</th>
                    <th>Rubro</th>
                    <th>Mejor Precio</th>
                    <th>Ganador</th>
                    <th>Ahorro</th>
                    <th>Estado</th>
                </tr>
            </thead>
            <tbody id="tableBody">
                <!-- JS Inject -->
            </tbody>
        </table>
    </div>
</div>

<script>
const app = {{
    data: {json_data},
    rubros: {rubros_json},
    competitors: {competidores_json},
    
    init() {{
        const select = document.getElementById('rubroFilter');
        this.rubros.forEach(r => {{
            const opt = document.createElement('option');
            opt.value = opt.innerText = r;
            select.appendChild(opt);
        }});
        this.render(this.data);
    }},

    fmt(n) {{
        return new Intl.NumberFormat('es-AR', {{ style: 'currency', currency: 'ARS', maximumFractionDigits: 0 }}).format(n);
    }},

    render(list) {{
        const body = document.getElementById('tableBody');
        body.innerHTML = '';
        
        list.slice(0, 300).forEach((p, i) => {{
            const tr = document.createElement('tr');
            tr.className = 'row-main';
            tr.onclick = () => this.toggle(i);
            
            const isOffer = p.Tipo_Ganador === 'OFERTA';
            const offerBadge = isOffer ? '<span class="badge-pill bg-offer">OFERTA</span>' : '';
            
            tr.innerHTML = `
                <td>
                    <div style="font-weight:600; color:white">${{p.Descripcion_Norm}}</div>
                    <div style="font-size:0.7rem; color:var(--text-muted)">SKU: ${{p.Material}}</div>
                </td>
                <td><span style="color:var(--text-muted)">${{p.Rubro}}</span></td>
                <td>
                    <div class="price-best" style="${{isOffer ? 'color:var(--warning)' : ''}}">
                        ${{this.fmt(p.Precio_Minimo)}}
                    </div>
                </td>
                <td><span style="font-weight:500">${{p.Ganador}}</span></td>
                <td><span class="badge-pill bg-saving">-${{p.Ahorro_Pct.toFixed(1)}}%</span></td>
                <td>${{offerBadge}}</td>
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
                            <div class="matrix-label">${{c}}</div>
                            <div class="matrix-value" style="${{win ? 'color:var(--success)' : ''}}">${{this.fmt(p[c])}}</div>
                        </div>
                    `;
                }}
            }});

            detail.innerHTML = `<td colspan="6"><div class="matrix-grid">${{matrixHtml}}</div></td>`;
            
            body.appendChild(tr);
            body.appendChild(detail);
        }});
    }},

    toggle(i) {{
        document.getElementById('detail-'+i).classList.toggle('active');
    }},

    filter() {{
        const q = document.getElementById('q').value.toLowerCase();
        const r = document.getElementById('rubroFilter').value;
        
        const filtered = this.data.filter(p => {{
            const matchQ = p.Descripcion_Norm.toLowerCase().includes(q) || p.Material.includes(q);
            const matchR = r === "" || p.Rubro === r;
            return matchQ && matchR;
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
    print(f"✅ Dashboard HTML Premium V3 (Control Panel) generado: {OUTPUT_HTML}")


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
        if pd.isna(min_val):
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
        df_pivot, competidores, tipo_mapping = limpiar_y_pivotar(df_raw)
        
        if not competidores:
            print("⚠️ No se detectaron columnas de competidores. Revisando Excel...")
        else:
            df_final = analizar_mercado(df_pivot, competidores, tipo_mapping)
            
            generar_reporte_consola(df_final)
            generar_archivos_finales(df_final)
            generar_html_premium(df_final, competidores)
            
            print("\n✅ CICLO COMPLETO FINALIZADO (V3.0 Vertical).")

if __name__ == "__main__":
    main()

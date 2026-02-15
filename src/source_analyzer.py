#!/usr/bin/env python3
"""
source_analyzer.py — Análisis de Código Fuente de Flybondi

Descarga el HTML de las páginas de resultados de Flybondi y analiza:
- Comentarios HTML (<!-- ... -->)
- Variables JavaScript con keywords relevantes
- Palabras clave: debug, promo, discount, todo, fixme, hack, test, beta
- Endpoints ocultos en el código
- Configuraciones hardcodeadas
- Versiones de la app y dependencias

Cada hallazgo se guarda en un archivo de hallazgos con timestamp.

Uso:
    python -m src.source_analyzer              # Análisis único
    python -m src.source_analyzer --loop       # Cada hora
    python -m src.source_analyzer --loop 360   # Cada 6 horas
    python -m src.source_analyzer --diff       # Comparar con análisis anterior

Se ejecuta en segundo plano sin intervención del usuario.
"""

import os
import sys
import re
import json
import time
import hashlib
import argparse
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from curl_cffi import requests as http
    USE_CURL = True
except ImportError:
    import requests as http
    USE_CURL = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
SOURCE_DIR = DATA_DIR / "source_analysis"
SOURCE_DIR.mkdir(parents=True, exist_ok=True)

SNAPSHOTS_DIR = SOURCE_DIR / "snapshots"
SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

FINDINGS_LOG = SOURCE_DIR / "findings.log"
FINDINGS_HISTORY = SOURCE_DIR / "findings_history.json"

# Páginas a analizar
PAGES_TO_ANALYZE = [
    {
        "name": "search_dates",
        "url": "https://flybondi.com/ar/search/dates?adults=2&children=0&currency=ARS&fromCityCode=BUE&infants=0&toCityCode=FLN&utm_origin=search_bar",
        "description": "Página de selección de fechas",
    },
    {
        "name": "search_results",
        "url": "https://flybondi.com/ar/search/results?adults=2&children=0&currency=ARS&departureDate=2026-03-09&returnDate=2026-03-16&fromCityCode=BUE&infants=0&toCityCode=FLN",
        "description": "Página de resultados de búsqueda",
    },
    {
        "name": "home_ar",
        "url": "https://flybondi.com/ar",
        "description": "Home Argentina",
    },
    {
        "name": "home_br",
        "url": "https://flybondi.com/br",
        "description": "Home Brasil",
    },
]

# Keywords a buscar (case-insensitive)
KEYWORDS = {
    "high_priority": [
        "debug", "promo", "discount", "todo", "fixme", "hack",
        "test_mode", "staging", "beta_feature", "internal_only",
        "price_override", "manual_price", "force_price",
        "admin_only", "dev_mode", "feature_flag", "experiment",
        "secret", "hidden", "deprecated_but_active",
    ],
    "medium_priority": [
        "coupon", "voucher", "credit", "reward", "loyalty",
        "club_member", "vip", "special_offer", "flash_sale",
        "early_bird", "last_minute", "hot_deal",
        "promotion", "campaign", "sale_price", "original_price",
        "markup", "margin", "commission", "fee_override",
        "bundle", "pack", "combo", "upgrade_free",
    ],
    "low_priority": [
        "todo", "fixme", "xxx", "bug", "workaround",
        "temporary", "remove_later", "cleanup",
        "hardcode", "magic_number", "env_var",
        "api_endpoint", "webhook", "callback",
    ],
}

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "es-ES,es;q=0.9,en;q=0.8",
    "cache-control": "no-cache",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/144.0.0.0 Safari/537.36"
    ),
}


# ============================================================================
# TELEGRAM
# ============================================================================

def send_telegram(message: str, silent: bool = False) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
            "disable_notification": silent,
        }
        resp = http.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception:
        return False


# ============================================================================
# DESCARGA DE PÁGINAS
# ============================================================================

def download_page(url: str) -> tuple[str | None, int]:
    """Descarga el HTML de una página. Returns: (html_content, status_code)"""
    try:
        kwargs = {"headers": HEADERS, "timeout": 30}
        if USE_CURL:
            kwargs["impersonate"] = "chrome"

        resp = http.get(url, **kwargs)
        return resp.text, resp.status_code

    except Exception as e:
        print(f"   ❌ Error descargando {url}: {e}")
        return None, 0


# ============================================================================
# ANÁLISIS DE CÓDIGO FUENTE
# ============================================================================

def analyze_html_comments(html: str) -> list[dict]:
    """Extrae y analiza comentarios HTML."""
    findings = []

    # Buscar todos los comentarios HTML
    comments = re.findall(r'<!--(.*?)-->', html, re.DOTALL)

    for comment in comments:
        comment_clean = comment.strip()

        # Ignorar comentarios triviales/de frameworks
        if len(comment_clean) < 5:
            continue
        if comment_clean.startswith("[if "):  # IE conditionals
            continue
        if comment_clean.startswith("!"):  # DOCTYPE comments
            continue

        # Buscar keywords en el comentario
        comment_lower = comment_clean.lower()
        matched_keywords = []

        for priority, keywords in KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in comment_lower:
                    matched_keywords.append({"keyword": kw, "priority": priority})

        # Si tiene keywords interesantes O es un comentario largo (posible debug info)
        if matched_keywords or len(comment_clean) > 100:
            findings.append({
                "type": "HTML_COMMENT",
                "content": comment_clean[:500],
                "length": len(comment_clean),
                "matched_keywords": matched_keywords,
                "priority": (
                    "HIGH" if any(k["priority"] == "high_priority" for k in matched_keywords)
                    else "MEDIUM" if any(k["priority"] == "medium_priority" for k in matched_keywords)
                    else "LOW"
                ),
            })

    return findings


def analyze_javascript(html: str) -> list[dict]:
    """Analiza scripts inline y URLs de scripts externos."""
    findings = []

    # === 1. Scripts inline ===
    inline_scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)

    for script in inline_scripts:
        if len(script.strip()) < 10:
            continue

        script_lower = script.lower()
        matched_keywords = []

        for priority, keywords in KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in script_lower:
                    # Obtener contexto alrededor del keyword
                    pattern = re.compile(re.escape(kw), re.IGNORECASE)
                    for match in pattern.finditer(script):
                        start = max(0, match.start() - 80)
                        end = min(len(script), match.end() + 80)
                        context = script[start:end].strip()
                        matched_keywords.append({
                            "keyword": kw,
                            "priority": priority,
                            "context": context,
                        })

        if matched_keywords:
            findings.append({
                "type": "INLINE_SCRIPT",
                "script_length": len(script),
                "matched_keywords": matched_keywords[:20],  # Limitar
                "priority": (
                    "HIGH" if any(k["priority"] == "high_priority" for k in matched_keywords)
                    else "MEDIUM" if any(k["priority"] == "medium_priority" for k in matched_keywords)
                    else "LOW"
                ),
            })

    # === 2. Variables globales interesantes ===
    global_var_patterns = [
        r'window\.([A-Z_][A-Z_0-9]*)\s*=\s*(.{1,200})',
        r'window\["([^"]+)"\]\s*=\s*(.{1,200})',
        r'self\.([A-Z_][A-Z_0-9]*)\s*=\s*(.{1,200})',
        r'var\s+([A-Z_][A-Z_0-9]{3,})\s*=\s*(.{1,200})',
        r'const\s+([A-Z_][A-Z_0-9]{3,})\s*=\s*(.{1,200})',
    ]

    for pattern in global_var_patterns:
        for match in re.finditer(pattern, html):
            var_name = match.group(1)
            var_value = match.group(2).strip()[:200]
            var_lower = var_name.lower()

            # Verificar si el nombre de variable es interesante
            interesting = False
            matched_kws = []
            for priority, keywords in KEYWORDS.items():
                for kw in keywords:
                    if kw.lower() in var_lower:
                        interesting = True
                        matched_kws.append(kw)

            if interesting:
                findings.append({
                    "type": "GLOBAL_VARIABLE",
                    "variable_name": var_name,
                    "value_preview": var_value,
                    "matched_keywords": matched_kws,
                    "priority": "HIGH" if any(
                        kw in KEYWORDS["high_priority"] for kw in matched_kws
                    ) else "MEDIUM",
                })

    # === 3. URLs de API / endpoints ocultos ===
    api_patterns = [
        r'["\']((https?://[^"\']*(?:api|graphql|webhook|callback|internal|admin|debug|staging|beta)[^"\']*))["\'"]',
        r'["\']((https?://[^"\']*flybondi[^"\']*(?:experiment|config|feature|flag|toggle)[^"\']*))["\'"]',
        r'["\']((/?(?:api|internal|admin|debug|staging)/[^"\']+))["\']',
    ]

    seen_urls = set()
    for pattern in api_patterns:
        for match in re.finditer(pattern, html, re.IGNORECASE):
            url = match.group(1)
            if url not in seen_urls and len(url) > 10:
                seen_urls.add(url)
                findings.append({
                    "type": "HIDDEN_ENDPOINT",
                    "url": url[:500],
                    "priority": "HIGH" if any(
                        kw in url.lower() for kw in ["admin", "debug", "internal", "staging"]
                    ) else "MEDIUM",
                })

    # === 4. Configuraciones hardcodeadas ===
    config_patterns = [
        (r'"(STRIPE_[A-Z_]+)"\s*:\s*"([^"]+)"', "PAYMENT_CONFIG"),
        (r'"(MERCADOPAGO_[A-Z_]+)"\s*:\s*"([^"]+)"', "PAYMENT_CONFIG"),
        (r'"(API_KEY)"\s*:\s*"([^"]+)"', "API_KEY_EXPOSED"),
        (r'"(SECRET_[A-Z_]+)"\s*:\s*"([^"]+)"', "SECRET_EXPOSED"),
        (r'"(TOKEN)"\s*:\s*"([^"]+)"', "TOKEN_EXPOSED"),
    ]

    for pattern, config_type in config_patterns:
        for match in re.finditer(pattern, html, re.IGNORECASE):
            findings.append({
                "type": config_type,
                "key": match.group(1),
                "value_preview": match.group(2)[:50] + "..." if len(match.group(2)) > 50 else match.group(2),
                "priority": "HIGH",
            })

    # === 5. Versión de la app y metadata ===
    version_patterns = [
        (r'"version"\s*:\s*"([^"]+)"', "APP_VERSION"),
        (r'"buildId"\s*:\s*"([^"]+)"', "BUILD_ID"),
        (r'"commitHash"\s*:\s*"([^"]+)"', "COMMIT_HASH"),
        (r'x-fo-ui-version["\s:]+(["\']?)([^"\'>\s,}]+)\1', "UI_VERSION"),
    ]

    for pattern, meta_type in version_patterns:
        for match in re.finditer(pattern, html, re.IGNORECASE):
            value = match.group(2) if len(match.groups()) > 1 else match.group(1)
            findings.append({
                "type": "METADATA",
                "meta_type": meta_type,
                "value": value[:100],
                "priority": "LOW",
            })

    return findings


def analyze_page(page: dict) -> dict:
    """Analiza una página completa."""
    name = page["name"]
    url = page["url"]
    description = page["description"]

    print(f"\n   📄 Analizando: {name} ({description})")

    html, status = download_page(url)

    result = {
        "name": name,
        "url": url,
        "description": description,
        "status_code": status,
        "timestamp": datetime.now().isoformat(),
        "findings": [],
    }

    if not html:
        result["error"] = "No se pudo descargar"
        print(f"      ❌ No se pudo descargar")
        return result

    result["html_size"] = len(html)
    result["html_hash"] = hashlib.md5(html.encode()).hexdigest()

    # Analizar comentarios HTML
    comment_findings = analyze_html_comments(html)
    result["findings"].extend(comment_findings)

    # Analizar JavaScript
    js_findings = analyze_javascript(html)
    result["findings"].extend(js_findings)

    # Contar por prioridad
    high = [f for f in result["findings"] if f.get("priority") == "HIGH"]
    medium = [f for f in result["findings"] if f.get("priority") == "MEDIUM"]
    low = [f for f in result["findings"] if f.get("priority") == "LOW"]

    if high:
        print(f"      🚨 {len(high)} hallazgos de alta prioridad")
    if medium:
        print(f"      ⚠️  {len(medium)} hallazgos de media prioridad")
    if low:
        print(f"      ℹ️  {len(low)} hallazgos de baja prioridad")
    if not result["findings"]:
        print(f"      ✅ Sin hallazgos relevantes")

    return result


# ============================================================================
# COMPARACIÓN CON ANÁLISIS ANTERIOR
# ============================================================================

def load_previous_analysis() -> dict | None:
    """Carga el análisis anterior para comparar."""
    if FINDINGS_HISTORY.exists():
        try:
            data = json.loads(FINDINGS_HISTORY.read_text(encoding="utf-8"))
            return data
        except (json.JSONDecodeError, OSError):
            return None
    return None


def detect_source_changes(old: dict | None, new: dict) -> list[dict]:
    """Detecta cambios entre dos análisis de código fuente."""
    if old is None:
        return []

    changes = []
    old_pages = {p["name"]: p for p in old.get("pages", [])}
    new_pages = {p["name"]: p for p in new.get("pages", [])}

    for name, new_page in new_pages.items():
        old_page = old_pages.get(name)
        if not old_page:
            changes.append({
                "type": "NEW_PAGE",
                "page": name,
                "description": f"Nueva página analizada: {name}",
            })
            continue

        # ¿Cambió el HTML?
        if new_page.get("html_hash") != old_page.get("html_hash"):
            changes.append({
                "type": "HTML_CHANGED",
                "page": name,
                "old_hash": old_page.get("html_hash"),
                "new_hash": new_page.get("html_hash"),
                "old_size": old_page.get("html_size", 0),
                "new_size": new_page.get("html_size", 0),
            })

        # ¿Hallazgos nuevos?
        old_findings_set = {
            f"{f.get('type')}:{f.get('content', f.get('variable_name', f.get('url', '')))[:100]}"
            for f in old_page.get("findings", [])
        }
        new_findings_set = {
            f"{f.get('type')}:{f.get('content', f.get('variable_name', f.get('url', '')))[:100]}"
            for f in new_page.get("findings", [])
        }

        new_only = new_findings_set - old_findings_set
        removed = old_findings_set - new_findings_set

        if new_only:
            changes.append({
                "type": "NEW_FINDINGS",
                "page": name,
                "count": len(new_only),
                "findings": list(new_only)[:10],
            })

        if removed:
            changes.append({
                "type": "REMOVED_FINDINGS",
                "page": name,
                "count": len(removed),
                "findings": list(removed)[:10],
            })

    return changes


# ============================================================================
# LOGGING
# ============================================================================

def append_findings_log(results: list[dict]):
    """Registra los hallazgos en el log."""
    with open(FINDINGS_LOG, "a", encoding="utf-8") as f:
        for page_result in results:
            page_name = page_result.get("name", "?")
            timestamp = page_result.get("timestamp", "?")

            for finding in page_result.get("findings", []):
                priority = finding.get("priority", "?")
                ftype = finding.get("type", "?")

                detail = ""
                if ftype == "HTML_COMMENT":
                    detail = finding.get("content", "")[:100]
                elif ftype == "GLOBAL_VARIABLE":
                    detail = f"{finding.get('variable_name', '?')} = {finding.get('value_preview', '?')}"
                elif ftype == "HIDDEN_ENDPOINT":
                    detail = finding.get("url", "?")
                elif ftype == "INLINE_SCRIPT":
                    kws = [k["keyword"] for k in finding.get("matched_keywords", [])[:5]]
                    detail = f"Keywords: {', '.join(kws)}"
                elif ftype == "METADATA":
                    detail = f"{finding.get('meta_type', '?')}: {finding.get('value', '?')}"
                else:
                    detail = finding.get("key", finding.get("value_preview", "?"))

                f.write(f"[{timestamp}] [{priority}] [{page_name}] {ftype} — {detail}\n")


# ============================================================================
# FLUJO PRINCIPAL
# ============================================================================

def run_analysis(compare: bool = False):
    """Ejecuta un análisis completo del código fuente."""
    now = datetime.now()
    print(f"\n{'=' * 70}")
    print(f"🔬 SOURCE ANALYZER — {now.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"{'=' * 70}")

    # Cargar análisis anterior
    previous = load_previous_analysis()

    # Analizar todas las páginas
    page_results = []
    for page in PAGES_TO_ANALYZE:
        result = analyze_page(page)
        page_results.append(result)
        time.sleep(2)  # Pausa entre descargas

    # Consolidar resultados
    all_findings = []
    for pr in page_results:
        all_findings.extend(pr.get("findings", []))

    high = [f for f in all_findings if f.get("priority") == "HIGH"]
    medium = [f for f in all_findings if f.get("priority") == "MEDIUM"]
    low = [f for f in all_findings if f.get("priority") == "LOW"]

    print(f"\n{'=' * 70}")
    print(f"📊 RESUMEN DE ANÁLISIS")
    print(f"{'=' * 70}")
    print(f"   Páginas analizadas: {len(page_results)}")
    print(f"   Total hallazgos: {len(all_findings)}")
    print(f"   🚨 Alta prioridad: {len(high)}")
    print(f"   ⚠️  Media prioridad: {len(medium)}")
    print(f"   ℹ️  Baja prioridad: {len(low)}")

    # Mostrar hallazgos de alta prioridad
    if high:
        print(f"\n{'─' * 70}")
        print(f"🚨 HALLAZGOS DE ALTA PRIORIDAD:")
        print(f"{'─' * 70}")
        for f in high:
            ftype = f.get("type", "?")
            if ftype == "HTML_COMMENT":
                print(f"\n   📝 Comentario HTML:")
                print(f"      {f.get('content', '')[:200]}")
            elif ftype == "GLOBAL_VARIABLE":
                print(f"\n   🔧 Variable global: {f.get('variable_name', '?')}")
                print(f"      Valor: {f.get('value_preview', '?')[:150]}")
            elif ftype == "HIDDEN_ENDPOINT":
                print(f"\n   🔗 Endpoint oculto: {f.get('url', '?')[:200]}")
            elif ftype in ("API_KEY_EXPOSED", "SECRET_EXPOSED", "TOKEN_EXPOSED", "PAYMENT_CONFIG"):
                print(f"\n   🔑 {ftype}: {f.get('key', '?')} = {f.get('value_preview', '?')}")
            elif ftype == "INLINE_SCRIPT":
                keywords = [k["keyword"] for k in f.get("matched_keywords", [])[:5]]
                print(f"\n   📜 Script con keywords: {', '.join(keywords)}")
                for kw in f.get("matched_keywords", [])[:3]:
                    print(f"      Contexto: ...{kw.get('context', '')[:150]}...")

    # Comparar con análisis anterior
    if compare and previous:
        changes = detect_source_changes(previous, {"pages": page_results})
        if changes:
            print(f"\n{'─' * 70}")
            print(f"🔄 CAMBIOS DESDE EL ÚLTIMO ANÁLISIS:")
            print(f"{'─' * 70}")
            for ch in changes:
                if ch["type"] == "HTML_CHANGED":
                    size_diff = ch.get("new_size", 0) - ch.get("old_size", 0)
                    sign = "+" if size_diff >= 0 else ""
                    print(f"   📄 {ch['page']} — HTML cambió ({sign}{size_diff} bytes)")
                elif ch["type"] == "NEW_FINDINGS":
                    print(f"   🆕 {ch['page']} — {ch['count']} hallazgos nuevos")
                elif ch["type"] == "REMOVED_FINDINGS":
                    print(f"   🗑️  {ch['page']} — {ch['count']} hallazgos removidos")

            # Alertar por Telegram si hay cambios significativos
            html_changes = [c for c in changes if c["type"] == "HTML_CHANGED"]
            new_findings = [c for c in changes if c["type"] == "NEW_FINDINGS"]

            if html_changes or new_findings:
                msg = f"🔬 *SOURCE CHANGE ALERT — Flybondi*\n\n"

                if html_changes:
                    msg += f"*Código fuente modificado:*\n"
                    for c in html_changes:
                        size_diff = c.get("new_size", 0) - c.get("old_size", 0)
                        sign = "+" if size_diff >= 0 else ""
                        msg += f"   • `{c['page']}` ({sign}{size_diff} bytes)\n"
                    msg += "\n"

                if new_findings:
                    msg += f"*Nuevos hallazgos:*\n"
                    for c in new_findings:
                        msg += f"   • `{c['page']}`: {c['count']} hallazgo(s) nuevo(s)\n"
                    msg += "\n"

                msg += f"🕐 {now.strftime('%d/%m/%Y %H:%M')}"
                send_telegram(msg, silent=True)

        else:
            print(f"\n   ✅ Sin cambios desde el último análisis")

    # Registrar en log
    append_findings_log(page_results)
    print(f"\n   💾 Hallazgos registrados en: {FINDINGS_LOG.name}")

    # Guardar snapshot del HTML
    for pr in page_results:
        if pr.get("html_size"):
            # No guardamos el HTML completo, solo un hash y los findings
            pass

    # Guardar análisis completo como historial
    analysis_data = {
        "timestamp": now.isoformat(),
        "pages": page_results,
        "total_findings": len(all_findings),
        "high_priority": len(high),
        "medium_priority": len(medium),
        "low_priority": len(low),
    }

    FINDINGS_HISTORY.write_text(
        json.dumps(analysis_data, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    # Guardar snapshot con timestamp
    snapshot_file = SOURCE_DIR / f"analysis_{now.strftime('%Y%m%d_%H%M%S')}.json"
    snapshot_file.write_text(
        json.dumps(analysis_data, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"   💾 Snapshot: {snapshot_file.name}")

    # Alertar si hay hallazgos de alta prioridad en primera ejecución
    if high and previous is None:
        msg = f"🔬 *SOURCE ANALYZER — Primer análisis*\n\n"
        msg += f"*{len(high)} hallazgo(s) de alta prioridad:*\n\n"

        for f in high[:5]:
            ftype = f.get("type", "?")
            if ftype == "HTML_COMMENT":
                msg += f"📝 Comentario: `{f.get('content', '')[:80]}`\n\n"
            elif ftype == "GLOBAL_VARIABLE":
                msg += f"🔧 Variable: `{f.get('variable_name', '?')}`\n\n"
            elif ftype == "HIDDEN_ENDPOINT":
                msg += f"🔗 Endpoint: `{f.get('url', '?')[:80]}`\n\n"
            elif ftype == "INLINE_SCRIPT":
                keywords = [k["keyword"] for k in f.get("matched_keywords", [])[:3]]
                msg += f"📜 Script keywords: `{', '.join(keywords)}`\n\n"
            else:
                msg += f"🔑 {ftype}: `{f.get('key', '?')}`\n\n"

        msg += f"🕐 {now.strftime('%d/%m/%Y %H:%M')}"
        send_telegram(msg, silent=True)

    # Guardar resumen simple para el monitor de precios
    save_simple_summary(all_findings, changes if compare and previous and changes else [])

    return analysis_data


def save_simple_summary(findings: list[dict], changes: list[dict]):
    """Guarda un resumen simple en texto para que lo lea el monitor de precios."""
    summary_file = DATA_DIR / "resumen_codigo.txt"
    
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write("<h3>🕵️ INTELIGENCIA DE CÓDIGO (Último escaneo)</h3>\n")
        
        # 1. Cambios recientes
        if changes:
            f.write("<div style='background:#fff3cd; padding:10px; border-radius:5px; margin-bottom:10px;'>")
            f.write("<strong>⚠️ CÓDIGO MODIFICADO RECIENTEMENTE:</strong><br>")
            f.write("<ul>")
            for c in changes:
                if c["type"] == "HTML_CHANGED":
                    diff = c.get("new_size", 0) - c.get("old_size", 0)
                    sign = "+" if diff > 0 else ""
                    f.write(f"<li>{c['page']}: <b>{sign}{diff} bytes</b> (Posible cambio de lógica/precios)</li>")
                elif c["type"] == "NEW_FINDINGS":
                    f.write(f"<li>{c['page']}: {c['count']} nuevos elementos sospechosos encontrados.</li>")
            f.write("</ul></div>")
        else:
             f.write("<p>✅ Sin cambios recientes en el código fuente.</p>\n")

        # 2. Hallazgos High Priority
        high = [x for x in findings if x.get("priority") == "HIGH"]
        if high:
            f.write(f"<p><strong>🚨 Se detectaron {len(high)} elementos de ALTA prioridad:</strong></p>")
            f.write("<ul>")
            for h in high[:5]: # Solo mostrar top 5
                tipo = h.get("type", "?")
                desc = h.get("content", h.get("variable_name", h.get("key", "?")))[:50]
                f.write(f"<li>[{tipo}] {desc}...</li>")
            f.write("</ul>")
            if len(high) > 5:
                f.write(f"<p><em>...y {len(high)-5} más.</em></p>")
        else:
            f.write("<p>✅ No hay amenazas de seguridad activas.</p>")



def run_loop(interval_minutes: int = 60):
    """Ejecuta el análisis en loop continuo."""
    print(f"\n🔄 MODO DAEMON — Analizando cada {interval_minutes} min")
    print(f"   Presioná Ctrl+C para detener\n")

    send_telegram(
        f"🔬 *Source Analyzer activado*\n\n"
        f"Intervalo: cada {interval_minutes} min\n"
        f"Analizando {len(PAGES_TO_ANALYZE)} páginas de Flybondi.",
        silent=True,
    )

    iteration = 0
    while True:
        try:
            iteration += 1
            print(f"\n{'#' * 70}")
            print(f"# ITERACIÓN #{iteration}")
            print(f"{'#' * 70}")

            run_analysis(compare=(iteration > 1))

            next_run = datetime.now() + timedelta(minutes=interval_minutes)
            print(f"\n⏳ Próximo análisis: {next_run.strftime('%H:%M:%S')}")
            time.sleep(interval_minutes * 60)

        except KeyboardInterrupt:
            print("\n\n🛑 Source Analyzer detenido.")
            send_telegram("🛑 Source Analyzer detenido.", silent=True)
            break


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="🔬 Analizador de Código Fuente de Flybondi",
    )
    parser.add_argument(
        "--loop", nargs="?", const=60, type=int, metavar="MIN",
        help="Modo daemon, analiza cada N minutos (default: 60)",
    )
    parser.add_argument(
        "--diff", action="store_true",
        help="Comparar con el análisis anterior",
    )
    parser.add_argument(
        "--no-telegram", action="store_true",
        help="No enviar alertas por Telegram",
    )

    args = parser.parse_args()

    if args.no_telegram:
        global TELEGRAM_BOT_TOKEN
        TELEGRAM_BOT_TOKEN = ""

    if args.loop is not None:
        run_loop(args.loop)
    else:
        run_analysis(compare=args.diff)


if __name__ == "__main__":
    main()

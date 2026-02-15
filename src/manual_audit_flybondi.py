# -*- coding: utf-8 -*-
import requests
import re
import sys
import json
from pathlib import Path

# Configurar encoding para Windows
sys.stdout.reconfigure(encoding='utf-8')

BUNDLE_URL = "https://flybondi.com/static/js/bundle.18bfad73.js"

print(f"DOWNLOADING {BUNDLE_URL}...")

try:
    r = requests.get(BUNDLE_URL, timeout=30)
    if r.status_code != 200:
        print(f"Error downloading: {r.status_code}")
        sys.exit(1)
        
    content = r.text
    print(f"Bundle size: {len(content)/1024/1024:.2f} MB")
    
    # --- PROMPT 1: GraphQL Mutations & Queries ---
    print("\n[PROMPT 1] GraphQL Hidden Queries/Mutations")
    print("-" * 50)
    
    # Buscar patrones: mutation Name(...) o query Name(...)
    ops = re.findall(r'(mutation|query)\s+([A-Za-z0-9_]+)\s*\(', content)
    unique_ops = sorted(list(set([f"{t.upper()} {n}" for t, n in ops])))
    
    print(f"Found {len(unique_ops)} operations. Top 20:")
    for op in unique_ops[:20]:
        print(f"  - {op}")

    # Buscar palabras clave en mutaciones
    sensitive_kws = ['Add', 'Remove', 'Update', 'Create', 'Purchase', 'Payment', 'Discount', 'Promo']
    print("\nSensitive Mutations:")
    for kw in sensitive_kws:
        # Buscar contexto de mutation...Name...
        matches = re.findall(r'mutation\s+[A-Za-z0-9_]*' + kw + r'[A-Za-z0-9_]*', content, re.IGNORECASE)
        for m in list(set(matches))[:5]:
             print(f"  - {m}")

    # --- PROMPT 2: Discount Logic ---
    print("\n[PROMPT 2] Discount Logic Analysis")
    print("-" * 50)
    
    # Buscar referencias a descuentos
    discounts = re.findall(r'\"([a-zA-Z0-9_]*(?:discount|promo|coupon|voucher)[a-zA-Z0-9_]*)\"', content, re.IGNORECASE)
    unique_discounts = sorted(list(set([d for d in discounts if len(d) > 4 and len(d) < 40])))
    
    print(f"Found {len(unique_discounts)} discount references. Sample:")
    for d in unique_discounts[:15]:
        print(f"  - {d}")

    if "uba" in content.lower():
        print("\n  UBA specific references found:")
        uba_refs = re.findall(r'.{0,30}uba.{0,30}', content, re.IGNORECASE)
        for ref in list(set(uba_refs))[:5]:
            print(f"    ...{ref.strip()}...")

    # --- PROMPT 4: Session & Cookies ---
    print("\n[PROMPT 4] Session Management")
    print("-" * 50)
    
    local_storage = re.findall(r'localStorage\.getItem\([\"\']([^\"\']+)[\"\']\)', content)
    print("localStorage Keys used:")
    for k in sorted(list(set(local_storage))):
        print(f"  - {k}")
        
    cookies = re.findall(r'document\.cookie\s*=\s*[\"\']([^\"\']+)[\"\']', content)
    if cookies:
        print("Cookie setting logic found:")
        for c in cookies:
            print(f"  - {c}")

    # --- PROMPT 6: Feature Flags ---
    print("\n[PROMPT 6] Feature Flags")
    print("-" * 50)
    
    # Buscar patrones comunes de flags
    flags = re.findall(r'[\"\'](enable_[a-z0-9_]+)[\"\']', content)
    flags += re.findall(r'[\"\'](is_[a-z0-9_]+_enabled)[\"\']', content)
    # Patrones de GrowthBook o similares
    flags += re.findall(r'\.isOn\([\"\']([^\"\']+)[\"\']\)', content)
    
    unique_flags = sorted(list(set(flags)))
    print(f"Found {len(unique_flags)} potential flags:")
    for f in unique_flags:
        print(f"  - {f}")

    # --- API Endpoints ---
    print("\n[EXTRA] API Endpoints Discovery")
    print("-" * 50)
    endpoints = re.findall(r'[\"\']((?:https?://|/api/)[^\"\']+)[\"\']', content)
    unique_endpoints = sorted(list(set([e for e in endpoints if len(e) < 100 and not e.startswith("http://www.w3.org")])))
    for e in unique_endpoints[:15]:
        print(f"  - {e}")

except Exception as e:
    print(f"ERROR: {e}")

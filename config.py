#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONFIGURACIÓN DE SCRAPERS - Sistema Centralizado
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuración de Yaguar
YAGUAR_CONFIG = {
    "username": os.getenv("YAGUAR_USERNAME", "Martin"),
    "password": os.getenv("YAGUAR_PASSWORD", "Martin2025"),
    "base_url": "https://yaguar.com.ar",
    "login_url": "https://yaguar.com.ar/login/",
    "categories": [
        {"slug": "almacen", "nombre": "Almacén"},
        {"slug": "bazar", "nombre": "Bazar"},
        {"slug": "bebidas", "nombre": "Bebidas"},
        {"slug": "bodega", "nombre": "Bodega"},
        {"slug": "desayuno", "nombre": "Desayuno"},
        {"slug": "frescos", "nombre": "Frescos"},
        {"slug": "kiosco", "nombre": "Kiosco"},
        {"slug": "limpieza", "nombre": "Limpieza"},
        {"slug": "mascotas", "nombre": "Mascotas"},
        {"slug": "papeles", "nombre": "Papeles"},
        {"slug": "perfumeria", "nombre": "Perfumería"},
    ],
    "headers": {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "accept-language": "es-ES,es;q=0.9,en;q=0.8",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Safari/605.1.15",
        "referer": "https://yaguar.com.ar/",
    },
    "impersonate": "safari15_3",
    "delay_entre_paginas": 1.0,
    "delay_entre_categorias": 2.0,
    "min_products_expected": 1000
}

# Configuración de MaxiCarrefour
MAXICARREFOUR_CONFIG = {
    "base_url": "https://comerciante.carrefour.com.ar",
    "cookies": {
        "PHPSESSID": os.getenv("CARREFOUR_PHPSESSID", ""),
        "cf_clearance": os.getenv("CARREFOUR_CF_CLEARANCE", "")
    },
    "headers": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9",
        "Referer": "https://comerciante.carrefour.com.ar/",
    },
    "sectores": [
        ("Bebidas", "bebidas"),
        ("Almacen", "almacen"),
        ("Desayuno y Merienda", "desayuno-y-merienda"),
        ("Limpieza", "limpieza"),
        ("Perfumeria", "perfumeria"),
        ("Lacteos y Frescos", "lacteos-y-productos-frescos"),
        ("Mundo Bebe", "mundo-bebe"),
        ("Mascotas", "mascotas"),
        ("Panaderia", "panaderia"),
        ("Bazar y Textil", "bazar-y-textil"),
    ],
    "productos_por_pagina": 24,
    "delay": 0.5,
    "min_products_expected": 500
}

# Configuración de Maxiconsumo
MAXICONSUMO_CONFIG = {
    "base_url": "https://maxiconsumo.com",
    "headers": {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'accept-language': 'es-ES,es;q=0.9,en;q=0.8',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Safari/605.1.15'
    },
    "impersonate": "safari15_3",
    "sucursal": "sucursal_burzaco",
    "categories": [
        "almacen", "bebidas", "bazar", "desayuno", "frescos", 
        "kiosco", "limpieza", "mascotas", "papeles", "perfumeria"
    ],
    "min_products_expected": 500,
    "maestro_limit": 300
}

# Configuración General
GENERAL_CONFIG = {
    "base_dir": os.path.dirname(os.path.abspath(__file__)),
    "data_dir": "data",
    "logs_dir": "logs",
    "output_format": "json",
    "encoding": "utf-8",
    "timeout": 30,
    "max_retries": 3,
    "retry_delay": 2.0
}

def get_config(scraper_name):
    """Obtener configuración específica de un scraper"""
    configs = {
        "yaguar": YAGUAR_CONFIG,
        "maxicarrefour": MAXICARREFOUR_CONFIG,
        "maxiconsumo": MAXICONSUMO_CONFIG
    }
    return configs.get(scraper_name.lower(), {})

def save_config_to_file(config_data, filename):
    """Guardar configuración a archivo JSON"""
    config_file = os.path.join(GENERAL_CONFIG["base_dir"], "config", f"{filename}.json")
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)
    
    print(f"Configuración guardada en: {config_file}")

def load_config_from_file(filename):
    """Cargar configuración desde archivo JSON"""
    config_file = os.path.join(GENERAL_CONFIG["base_dir"], "config", f"{filename}.json")
    
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def update_yaguar_credentials(username, password):
    """Actualizar credenciales de Yaguar"""
    YAGUAR_CONFIG["username"] = username
    YAGUAR_CONFIG["password"] = password
    save_config_to_file(YAGUAR_CONFIG, "yaguar")
    print("Credenciales de Yaguar actualizadas")

def update_maxicarrefour_cookies(phpsessid, cf_clearance):
    """Actualizar cookies de MaxiCarrefour"""
    MAXICARREFOUR_CONFIG["cookies"]["PHPSESSID"] = phpsessid
    MAXICARREFOUR_CONFIG["cookies"]["cf_clearance"] = cf_clearance
    save_config_to_file(MAXICARREFOUR_CONFIG, "maxicarrefour")
    print("Cookies de MaxiCarrefour actualizadas")

def setup_config():
    """Configuración inicial del sistema"""
    print("=== CONFIGURACIÓN DE SCRAPERS ===")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Crear directorio de configuración
    config_dir = os.path.join(GENERAL_CONFIG["base_dir"], "config")
    os.makedirs(config_dir, exist_ok=True)
    
    # Guardar configuraciones por defecto
    save_config_to_file(YAGUAR_CONFIG, "yaguar")
    save_config_to_file(MAXICARREFOUR_CONFIG, "maxicarrefour")
    save_config_to_file(MAXICONSUMO_CONFIG, "maxiconsumo")
    save_config_to_file(GENERAL_CONFIG, "general")
    
    print("Configuraciones guardadas en /config/")
    print()
    print("Para actualizar credenciales:")
    print("  python -c \"from config import update_yaguar_credentials; update_yaguar_credentials('usuario', 'contraseña')\"")
    print()
    print("Para actualizar cookies de MaxiCarrefour:")
    print("  python -c \"from config import update_maxicarrefour_cookies; update_maxicarrefour_cookies('PHPSESSID', 'cf_clearance')\"")

if __name__ == "__main__":
    setup_config()

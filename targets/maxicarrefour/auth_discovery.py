#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DESCUBRIMIENTO DEL PROCESO DE LOGIN MAXICARREFOUR
"""

import requests
from bs4 import BeautifulSoup
import json
import re

class MaxiCarrefourAuthDiscovery:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://comerciante.carrefour.com.ar"
        
        # Headers para simular navegador real
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'es-ES,es;q=0.9,en;q=0.8',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1'
        }
        
        self.session.headers.update(self.headers)
        print("🔍 Iniciando descubrimiento de proceso de login...")
    
    def analizar_pagina_login(self):
        """Analizar la página de login para encontrar formularios y endpoints"""
        print("\n1️⃣ Analizando página de login...")
        
        try:
            # URLs posibles de login
            login_urls = [
                f"{self.base_url}/login",
                f"{self.base_url}/ingresar", 
                f"{self.base_url}/acceso",
                f"{self.base_url}/auth",
                f"{self.base_url}/session"
            ]
            
            for url in login_urls:
                print(f"\n🔍 Probando URL: {url}")
                try:
                    response = self.session.get(url, timeout=30)
                    print(f"   Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Buscar formularios de login
                        forms = soup.find_all('form')
                        print(f"   📝 Formularios encontrados: {len(forms)}")
                        
                        for i, form in enumerate(forms):
                            print(f"\n   Formulario {i+1}:")
                            
                            # Action del formulario
                            action = form.get('action', '')
                            method = form.get('method', 'GET')
                            print(f"     Action: {action}")
                            print(f"     Method: {method}")
                            
                            # Buscar inputs
                            inputs = form.find_all('input')
                            print(f"     Inputs: {len(inputs)}")
                            
                            for input_elem in inputs:
                                input_type = input_elem.get('type', 'text')
                                input_name = input_elem.get('name', '')
                                input_placeholder = input_elem.get('placeholder', '')
                                input_id = input_elem.get('id', '')
                                
                                print(f"       - {input_type}: name='{input_name}' id='{input_id}' placeholder='{input_placeholder}'")
                        
                        # Buscar scripts de login
                        scripts = soup.find_all('script')
                        for script in scripts:
                            if script.string and ('login' in script.string.lower() or 'auth' in script.string.lower()):
                                print(f"   📜 Script con login/auth encontrado")
                                # Extraer URLs de API
                                api_urls = re.findall(r'https?://[^\s"\']+', script.string)
                                for api_url in api_urls:
                                    if 'api' in api_url or 'auth' in api_url:
                                        print(f"       🌐 API URL: {api_url}")
                        
                        # Guardar HTML para análisis manual
                        with open(f'login_page_{url.split("/")[-1]}.html', 'w', encoding='utf-8') as f:
                            f.write(response.text)
                        print(f"   💾 HTML guardado: login_page_{url.split('/')[-1]}.html")
                        
                        # Si encontramos inputs de email/password, esta es la página correcta
                        has_credentials = any(
                            input_elem.get('type') in ['email', 'password'] 
                            for input_elem in soup.find_all('input')
                        )
                        
                        if has_credentials:
                            print(f"   ✅ Página de login válida encontrada!")
                            return url, soup
                    
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ Error general: {e}")
        
        return None, None
    
    def analizar_apis_javascript(self):
        """Analizar archivos JavaScript para encontrar endpoints de autenticación"""
        print("\n2️⃣ Analizando JavaScripts para APIs de auth...")
        
        try:
            # Cargar página principal para encontrar scripts
            response = self.session.get(self.base_url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Encontrar todos los scripts
            scripts = soup.find_all('script')
            
            for script in scripts:
                src = script.get('src', '')
                if src and ('auth' in src.lower() or 'login' in src.lower() or 'session' in src.lower()):
                    print(f"\n📜 Script de auth encontrado: {src}")
                    
                    try:
                        # Cargar el script
                        if src.startswith('http'):
                            script_url = src
                        else:
                            script_url = self.base_url + src if src.startswith('/') else self.base_url + '/' + src
                        
                        script_response = self.session.get(script_url, timeout=30)
                        script_content = script_response.text
                        
                        # Buscar endpoints de API
                        api_patterns = [
                            r'/api/[^"\']+', 
                            r'/auth/[^"\']+',
                            r'/login/[^"\']+',
                            r'/session/[^"\']+',
                            r'https?://[^"\']*api[^"\']*'
                        ]
                        
                        for pattern in api_patterns:
                            matches = re.findall(pattern, script_content)
                            for match in matches:
                                print(f"   🌐 API Endpoint: {match}")
                        
                        # Buscar funciones de login
                        login_functions = re.findall(r'function\s+(login|auth|signin|authenticate)[^}]*}', script_content, re.IGNORECASE)
                        for func in login_functions:
                            print(f"   🔧 Función de login: {func[:100]}...")
                            
                    except Exception as e:
                        print(f"   ❌ Error cargando script: {e}")
                        
        except Exception as e:
            print(f"❌ Error analizando JavaScripts: {e}")
    
    def probar_endpoints_auth(self):
        """Probar endpoints comunes de autenticación"""
        print("\n3️⃣ Probando endpoints de autenticación...")
        
        # Endpoints comunes para probar
        auth_endpoints = [
            '/api/auth/login',
            '/api/v1/auth/login', 
            '/api/session/login',
            '/login/api',
            '/auth/login',
            '/api/user/login',
            '/api/authentication/login',
            '/api/login/validate',
            '/api/auth/signin'
        ]
        
        for endpoint in auth_endpoints:
            url = self.base_url + endpoint
            print(f"\n🔍 Probando endpoint: {url}")
            
            try:
                # Probar GET
                response = self.session.get(url, timeout=10)
                print(f"   GET Status: {response.status_code}")
                
                # Probar POST con datos dummy
                dummy_data = {
                    'email': 'test@test.com',
                    'password': 'test123',
                    'username': 'test',
                    'user': 'test',
                    'pass': 'test123'
                }
                
                response = self.session.post(url, data=dummy_data, timeout=10)
                print(f"   POST Status: {response.status_code}")
                
                if response.status_code != 404:
                    print(f"   ✅ Endpoint existe!")
                    print(f"   📄 Content-Type: {response.headers.get('content-type', 'N/A')}")
                    print(f"   📄 Content-Length: {len(response.text)}")
                    
                    # Si responde con JSON, mostrar estructura
                    if 'application/json' in response.headers.get('content-type', ''):
                        try:
                            json_data = response.json()
                            print(f"   📋 JSON Response: {str(json_data)[:200]}...")
                        except:
                            pass
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    def descubrir_proceso_completo(self):
        """Ejecutar descubrimiento completo del proceso de login"""
        print("🔍 DESCUBRIMIENTO COMPLETO DEL PROCESO DE LOGIN")
        print("=" * 60)
        
        # 1. Analizar página de login
        login_url, login_soup = self.analizar_pagina_login()
        
        # 2. Analizar JavaScripts
        self.analizar_apis_javascript()
        
        # 3. Probar endpoints
        self.probar_endpoints_auth()
        
        # 4. Resumen
        print("\n📋 RESUMEN DEL DESCUBRIMIENTO:")
        if login_url:
            print(f"✅ Página de login encontrada: {login_url}")
            
            # Extraer información del formulario
            if login_soup:
                forms = login_soup.find_all('form')
                for i, form in enumerate(forms):
                    action = form.get('action', '')
                    method = form.get('method', 'GET')
                    inputs = form.find_all('input')
                    
                    email_input = None
                    password_input = None
                    
                    for input_elem in inputs:
                        input_type = input_elem.get('type', '')
                        input_name = input_elem.get('name', '')
                        
                        if input_type == 'email' or 'email' in input_name.lower():
                            email_input = input_name
                        elif input_type == 'password' or 'password' in input_name.lower():
                            password_input = input_name
                    
                    if email_input and password_input:
                        print(f"🎯 Formulario válido encontrado:")
                        print(f"   Action: {action}")
                        print(f"   Method: {method}")
                        print(f"   Email field: {email_input}")
                        print(f"   Password field: {password_input}")
                        
                        return {
                            'login_url': login_url,
                            'form_action': action,
                            'form_method': method,
                            'email_field': email_input,
                            'password_field': password_input
                        }
        else:
            print("❌ No se encontró página de login válida")
            return None

if __name__ == "__main__":
    discovery = MaxiCarrefourAuthDiscovery()
    auth_info = discovery.descubrir_proceso_completo()
    
    if auth_info:
        print(f"\n🎉 INFORMACIÓN DE AUTENTICACIÓN DESCUBIERTA:")
        print(f"📋 Para implementar el login, necesitarás:")
        print(f"   1. URL: {auth_info['login_url']}")
        print(f"   2. Form Action: {auth_info['form_action']}")
        print(f"   3. Method: {auth_info['form_method']}")
        print(f"   4. Email Field: {auth_info['email_field']}")
        print(f"   5. Password Field: {auth_info['password_field']}")
        print(f"\n🔐 Podés implementar el scraper con estas credenciales")
    else:
        print(f"\n❌ No se pudo descubrir el proceso de login automáticamente")
        print(f"🔍 Revisa los archivos HTML guardados para análisis manual")

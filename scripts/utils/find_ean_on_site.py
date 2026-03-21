import requests
import re
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_product_links(category_url):
    r = requests.get(category_url, headers=HEADERS)
    soup = BeautifulSoup(r.text, 'html.parser')
    links = []
    for a in soup.select('.product-item-link')[:3]:
        links.append(a['href'])
    return links

def find_ean(product_url):
    print(f"\n📄 Analizando: {product_url}")
    r = requests.get(product_url, headers=HEADERS)
    html = r.text
    
    # 1. Buscar en dataLayer (regex para EAN 13)
    ean_match = re.search(r'["\']ean["\']\s*:\s*["\'](\d{13})["\']', html)
    if not ean_match:
        ean_match = re.search(r'["\']sku["\']\s*:\s*["\'](\d{13})["\']', html) # a veces usan sku como ean
    
    # 2. Buscar cualquier numero de 13 digitos
    all_13 = re.findall(r'[^\d](\d{13})[^\d]', html)
    # Filtrar los que probablemente sean EANs (empiezan por 779 para Argentina)
    ar_eans = [e for e in all_13 if e.startswith("779")]
    
    # 3. Buscar meta tags
    soup = BeautifulSoup(html, 'html.parser')
    meta_ean = soup.find("meta", {"name": "product:ean"})
    meta_gtin = soup.find("meta", {"name": "product:gtin"})
    
    return {
        "dataLayer_ean": ean_match.group(1) if ean_match else None,
        "regex_13_digits": list(set(all_13)),
        "meta_ean": meta_ean['content'] if meta_ean else None,
        "meta_gtin": meta_gtin['content'] if meta_gtin else None
    }

cat_url = 'https://maxiconsumo.com/sucursal_burzaco/almacen/aceites-y-vinagres/aceites.html'
links = get_product_links(cat_url)
for link in links:
    result = find_ean(link)
    print(result)

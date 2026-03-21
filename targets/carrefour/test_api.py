import requests
import json

url = "https://comerciante.carrefour.com.ar/products?method=productsList&currentPage=1&itemsPerPage=12&currentUrl=sec/almacén"

headers = {
    'accept': '*/*',
    'accept-language': 'es-ES,es;q=0.9',
    'content-type': 'application/x-www-form-urlencoded',
    'cookie': r"_fbp=fb.2.1762720184774.210392897523026321.AQYBAQIA; vtex-search-anonymous=e8f94bfdb91c4a03b5f440bb28df389a; _dyid=-9061242199398614599; PHPSESSID=qir2kj35b0rknq9gng18oe2om0; _dy_soct=1774061404!1594828.0'1598112.-11341218'1792788.-1'2288309.-1'2745823.-7686485'2992584.-8398287'3571772.0!ct4f7cas2dhmi95tjdxl8za7evhkfwxr~3563031.-1; dtm_token_sc=AQAHbKSKVCWLkwELGIGQAQBFAQABAQCba06DqgEBAJwPTb1w; __cf_bm=0y0CR58Lv9rMH3MaPbw60KRBjSvObauEW6OGvB7FX5A-1774111999-1.0.1.1-qnpVRnc1i74LBdvJWwEmSUtB7D1GzzZ.Zb5Nb4PA4Vg3EUGScuX2y2ZjJiBAEo7StdIf.eaTVCQmnDooEsgmJ2qdolPVTz7CF8SNFE2tAdU; cf_clearance=Q4Mat6RQBSOQJc38Z8crKI3KHDrDcDywgpGp1omsjes-1774112409-1.2.1.1-fcAIEUR.I1K3punOTYR4TsKvVdcb8FAYviIn83nWwV23RFRTTL29UGRs057k1mpXwdCQnIovJ.ewHg_pgSgZxH5I8i3_ChW.dwodlGKCgyfYkwp42wYivb.IBuwS2w2HIaGj0Ks7.FZ.MiRaPQRmMEacp2U4WUFmlve32Dkdh_nnUp0RqoS.qk52PZXoZCK6k7Zqp4FbrMCrMjYztwH76LKpTt0pBjg_g2RUAtC73r0",
    'priority': 'u=1, i',
    'referer': 'https://comerciante.carrefour.com.ar/sec/almac%C3%A9n',
    'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36'
}

response = requests.get(url, headers=headers)

import re
print(f"Status Code: {response.status_code}")
prices = re.findall(r'data-price="([^"]+)"', response.text)
eans = re.findall(r'data-ean="([^"]+)"', response.text)
print(f"Prices found: {prices[:5]}")
print(f"EANs found: {eans[:5]}")

if "private" in response.text:
    print("WARNING: 'private' still found in response.")
else:
    print("No 'private' found in response.")



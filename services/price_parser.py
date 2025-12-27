# services/price_parser.py
from curl_cffi import requests as cffi_requests
from bs4 import BeautifulSoup
import re

def search_atb(query: str):
    """
    Шукає товар в АТБ (Location ID: 1158 - Чернігів).
    Використовує curl_cffi для імітації TLS-відбитка Chrome.
    """
    
    base_url = "https://www.atbmarket.com/sch"
    params = {
        'lang': 'uk',
        'location': '1158',
        'query': query
    }

    try:
        response = cffi_requests.get(
            base_url, 
            params=params, 
            impersonate="chrome120",
            timeout=15
        )
        
        if response.status_code != 200:
            return f"⚠️ АТБ блокує (код {response.status_code})"

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Шукаємо картки
        items = soup.select('.catalog-item') 

        if not items:
            return "🤷‍♂️ В АТБ (маг. 1158) нічого не знайдено."

        results = []
        for item in items[:7]: 
            try:
                # --- НАЗВА ---
                name_tag = item.select_one('.catalog-item__title')
                if not name_tag: continue
                name = name_tag.get_text(strip=True)

                # --- ЦІНА ---
                price_final = "???"
                
                # Варіант 1: Топ/Боттом ціна
                price_top = item.select_one('.product-price__top')
                price_bottom = item.select_one('.product-price__bottom') 

                if price_top and price_bottom:
                    p_m = re.sub(r'[^\d]', '', price_top.get_text())
                    p_c = re.sub(r'[^\d]', '', price_bottom.get_text())
                    price_final = f"{p_m}.{p_c} грн"
                
                # Варіант 2: Ціна одним шматком
                elif item.select_one('.product-price__value'):
                    raw_text = item.select_one('.product-price__value').get_text(strip=True)
                    match = re.search(r'\d+[.,]\d+', raw_text)
                    if match:
                        price_final = f"{match.group().replace(',', '.')} грн"

                # --- АКЦІЯ ---
                is_sale = bool(item.select_one('.product-price__sale'))
                marker = "🔥" if is_sale else "📦"
                
                if price_final == "???":
                    price_final = "Немає в наявності"
                    marker = "⛔️"

                results.append(f"{marker} <b>{name}</b> — {price_final}")
                
            except Exception:
                continue
            
        return "\n".join(results) if results else "🤷‍♂️ Пусто."

    except Exception as e:
        return f"❌ Помилка з'єднання: {e}"

if __name__ == "__main__":
    print("🔎 Тестуємо новий метод обходу...")
    print(search_atb("хліб"))
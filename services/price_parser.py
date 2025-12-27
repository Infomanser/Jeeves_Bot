# services/price_parser.py
import cloudscraper
from bs4 import BeautifulSoup
import re
import time
import asyncio

def search_atb(query: str):
    """
    Шукає товар в АТБ (Location ID: 1158 - Чернігів).
    Використовує cloudscraper + прогрів сесії (Cookies).
    """
    
    # Створюємо скрапер
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )

    try:

        scraper.get("https://www.atbmarket.com/", timeout=10)
        
        time.sleep(10) 

        # --- ПОШУК ---
        base_url = "https://www.atbmarket.com/sch"
        params = {
            'lang': 'uk',
            'location': '1158',
            'query': query
        }

        # Робимо запит вже з куками
        response = scraper.get(base_url, params=params, timeout=10)
        
        if response.status_code != 200:
            return f"⚠️ АТБ блокує (код {response.status_code}). Спробуй пізніше."

        soup = BeautifulSoup(response.text, 'html.parser')
        
        if "captcha" in soup.text.lower():
            return "🤖 АТБ вимагає капчу. Спробуй пізніше."

        items = soup.select('.catalog-item') 

        if not items:
            return "🤷‍♂️ В АТБ (маг. 1158) нічого не знайдено."

        results = []
        for item in items[:7]: 
            try:
                name_tag = item.select_one('.catalog-item__title')
                if not name_tag: continue
                name = name_tag.get_text(strip=True)

                price_final = "???"
                
                # Ціна
                price_top = item.select_one('.product-price__top')
                price_bottom = item.select_one('.product-price__bottom') 

                if price_top and price_bottom:
                    p_m = re.sub(r'[^\d]', '', price_top.get_text())
                    p_c = re.sub(r'[^\d]', '', price_bottom.get_text())
                    price_final = f"{p_m}.{p_c} грн"
                elif item.select_one('.product-price__value'):
                    raw_text = item.select_one('.product-price__value').get_text(strip=True)
                    match = re.search(r'\d+[.,]\d+', raw_text)
                    if match:
                        price_final = f"{match.group().replace(',', '.')} грн"

                # Акція
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
        return f"❌ Помилка: {e}"

if __name__ == "__main__":
    print(search_atb("хліб"))

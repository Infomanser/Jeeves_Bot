# services/price_parser.py
import cloudscraper
from bs4 import BeautifulSoup
import re

def search_atb(query: str):
    """
    Шукає товар в АТБ (Location ID: 1158 - Чернігів).
    V2.0: Посилене маскування заголовків.
    """
    
    # 1. Створюємо скрапер
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )

    base_url = "https://www.atbmarket.com/sch"
    
    # 2. ПАРАМЕТРИ
    params = {
        'lang': 'uk',
        'location': '1158',
        'query': query
    }

    # 3. ДОДАТКОВЕ МАСКУВАННЯ (Headers)
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "max-age=0",
        "Referer": "https://www.atbmarket.com/",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        # Передаємо headers у запит
        response = scraper.get(base_url, params=params, headers=headers)
        
        if response.status_code != 200:
            return f"⚠️ АТБ блокує (код {response.status_code}). Спробуй пізніше."

        soup = BeautifulSoup(response.text, 'html.parser')
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
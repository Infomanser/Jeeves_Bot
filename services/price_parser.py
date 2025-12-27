# services/price_parser.py
import cloudscraper
from bs4 import BeautifulSoup
import re

def search_atb(query: str):
    """
    Шукає товар в АТБ (Location ID: 1158 - Чернігів).
    Використовує cloudscraper та Regex для чистого виводу.
    """
    
    # 1. Створюємо імітацію браузера Chrome (щоб не отримати 403)
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )

    # 2. Налаштування пошуку
    base_url = "https://www.atbmarket.com/sch"
    params = {
        'lang': 'uk',
        'location': '1158',  # Твій магазин
        'query': query
    }
    
    try:
        response = scraper.get(base_url, params=params)
        
        if response.status_code != 200:
            return f"⚠️ АТБ відповів кодом {response.status_code}"

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Шукаємо картки товарів
        items = soup.select('.catalog-item') 

        if not items:
            return "🤷‍♂️ В АТБ (маг. 1158) нічого не знайдено."

        results = []
        # Беремо перші 7 товарів
        for item in items[:7]: 
            try:
                # --- НАЗВА ---
                name_tag = item.select_one('.catalog-item__title')
                if not name_tag: continue
                name = name_tag.get_text(strip=True)

                # --- ЦІНА (Очищення) ---
                price_final = "???"
                
                # Спробуємо знайти стандартну ціну (гривні + копійки)
                price_top = item.select_one('.product-price__top')
                price_bottom = item.select_one('.product-price__bottom') 

                if price_top and price_bottom:
                    # Видаляємо все, крім цифр
                    p_m = re.sub(r'[^\d]', '', price_top.get_text())
                    p_c = re.sub(r'[^\d]', '', price_bottom.get_text())
                    price_final = f"{p_m}.{p_c} грн"
                
                # Якщо ціна одним блоком
                elif item.select_one('.product-price__value'):
                    raw_text = item.select_one('.product-price__value').get_text(strip=True)
                    match = re.search(r'\d+[.,]\d+', raw_text)
                    if match:
                        price_final = f"{match.group().replace(',', '.')} грн"

                # --- АКЦІЯ ---
                is_sale = bool(item.select_one('.product-price__sale'))
                marker = "🔥" if is_sale else "📦"
                
                # --- ФІЛЬТР "НЕМАЄ В НАЯВНОСТІ" ---
                if price_final == "???":
                    # Можна поставити marker = "⛔️", або просто написати текстом
                    price_final = "Немає в наявності"
                    marker = "⛔️"

                results.append(f"{marker} <b>{name}</b> — {price_final}")
                
            except Exception:
                continue
            
        return "\n".join(results) if results else "🤷‍♂️ Пусто."

    except Exception as e:
        return f"❌ Помилка парсингу: {e}"

# ТЕСТ ЗАПУСК (Тільки якщо запускаєш файл напряму)
if __name__ == "__main__":
    test_query = "цукор"
    print(f"🔎 Шукаємо '{test_query}' в магазині 1158...")
    print(search_atb(test_query))
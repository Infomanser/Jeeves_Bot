# services/calendar_api.py
import json
import os
from datetime import datetime, timedelta

# Шлях до файлу
JSON_FILE = "calendar.json"

def load_events():
    """Завантажує події з файлу"""
    if not os.path.exists(JSON_FILE):
        return []
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_events(events):
    """Зберігає події у файл"""
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=4)

# --- ОСНОВНІ ФУНКЦІЇ ---

def get_events(filter_type: str):
    """
    filter_type: 'all', 'winter', 'spring', etc.
    Повертає відсортований список подій.
    """
    events = load_events()
    if not events: return []

    # Сортуємо: спершу розбиваємо дату "ДД.ММ"
    def sort_key(e):
        d, m = map(int, e['date'].split('.'))
        return m, d # Сортуємо по місяцю, потім по дню

    events.sort(key=sort_key)

    if filter_type == "all":
        return events
    
    # Фільтр по сезонах
    seasons = {
        "winter": [12, 1, 2],
        "spring": [3, 4, 5],
        "summer": [6, 7, 8],
        "autumn": [9, 10, 11]
    }
    
    target_months = seasons.get(filter_type, [])
    return [e for e in events if int(e['date'].split('.')[1]) in target_months]

def add_new_event(date: str, name: str, raw_link: str = "-"):
    """Додає нову подію"""
    events = load_events()
    
    # Генерація ID (просто макс + 1)
    new_id = max([e.get('id', 0) for e in events], default=0) + 1
    
    # Обробка лінка
    link = None
    if raw_link and raw_link != "-" and "http" in raw_link:
        link = raw_link.strip()

    new_event = {
        "id": new_id,
        "date": date,
        "text": name,
        "link": link
    }
    
    events.append(new_event)
    save_events(events)
    return new_event

def delete_event(query: str) -> str:
    """
    Видаляє подію за датою (14.02) або за назвою (частковий збіг).
    Повертає текстовий звіт.
    """
    events = load_events()
    initial_count = len(events)
    query = query.lower().strip()
    
    
    new_events = []
    deleted_names = []
    
    for e in events:
        # Перевірка на дату
        if e['date'] == query:
            deleted_names.append(f"{e['date']} ({e['text']})")
            continue
            
        # Перевірка на назву
        if query in e['text'].lower():
            deleted_names.append(f"{e['date']} ({e['text']})")
            continue
            
        new_events.append(e)
    
    if len(new_events) == initial_count:
        return "🤷‍♂️ Нічого не знайдено для видалення."
    
    save_events(new_events)
    return f"✅ Видалено {len(deleted_names)} подій:\n" + "\n".join(deleted_names)

def get_event_by_id(evt_id: int):
    events = load_events()
    for e in events:
        if e.get('id') == evt_id:
            return e
    return None

def update_event_text(evt_id: int, new_text: str):
    events = load_events()
    for e in events:
        if e.get('id') == evt_id:
            e['text'] = new_text
            save_events(events)
            return True
    return False

def mass_import_events(text_block: str):
    """
    Імпортує рядки виду:
    14.02 День закоханих
    """
    events = load_events()
    lines = text_block.strip().split('\n')
    count = 0
    next_id = max([e.get('id', 0) for e in events], default=0) + 1

    for line in lines:
        parts = line.strip().split(maxsplit=1)
        if len(parts) < 2: continue
        
        date_str = parts[0]
        text_str = parts[1]
        
        # Валідація дати груба
        if "." not in date_str: continue

        events.append({
            "id": next_id,
            "date": date_str,
            "text": text_str,
            "link": None
        })
        next_id += 1
        count += 1
        
    save_events(events)
    return count

# --- ДОПОМІЖНІ ---

def decode_event_to_string(event):
    """Робить красивий рядок з лінком або без"""
    txt = html_esc(event['text'])
    if event.get('link'):
        return f'<a href="{event["link"]}">{txt}</a>'
    return txt

def html_esc(text):
    import html
    return html.escape(text)

# --- ЛОГІКА НАГАДУВАНЬ ---

def check_upcoming_events() -> str:
    """
    Перевіряє події на Сьогодні, Завтра і Найближчий тиждень.
    Повертає відформатований текст або None, якщо подій немає.
    """
    events = load_events()
    if not events: return None
    
    today = datetime.now()
    
    list_today = []
    list_tomorrow = []
    list_week = [] # 2-7 дні
    
    for event in events:
        try:
            d, m = map(int, event['date'].split('.'))
        except: continue
        

        try:
            evt_date_this_year = datetime(today.year, m, d)
        except ValueError:
            # Якщо 29.02, а рік не високосний — ігноруємо або ставимо 01.03 (тут ігноруємо)
            continue
            

        
        if evt_date_this_year.date() < today.date():
             # Подія була в минулому, дивимось наступний рік
             evt_date_next = datetime(today.year + 1, m, d)
             delta = (evt_date_next.date() - today.date()).days
        else:
             delta = (evt_date_this_year.date() - today.date()).days
        
        # Розподіляємо по списках
        link_text = decode_event_to_string(event)
        
        if delta == 0:
            list_today.append(link_text)
        elif delta == 1:
            list_tomorrow.append(link_text)
        elif 2 <= delta <= 7:
            # Форматуємо: "05.01 - Назва"
            list_week.append(f"{event['date']} - {link_text}")
            
    # Формуємо звіт
    parts = []
    
    if list_today:
        parts.append(f"🔥 <b>СЬОГОДНІ:</b>\n" + "\n".join([f"• {x}" for x in list_today]))
        
    if list_tomorrow:
        parts.append(f"⚠️ <b>Завтра:</b>\n" + "\n".join([f"• {x}" for x in list_tomorrow]))
        
    if list_week:
        parts.append(f"👀 <b>На тижні:</b>\n" + "\n".join([f"• {x}" for x in list_week]))
        
    if not parts:
        return None
        
    return "\n\n".join(parts)

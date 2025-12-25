# services/calendar_api.py
import json
import os
import html
from datetime import datetime, timedelta

JSON_FILE = "calendar.json"

# --- РОБОТА З ФАЙЛОМ ---

def load_events():
    if not os.path.exists(JSON_FILE):
        return []
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_events(events):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=4)

# --- ОСНОВНА ЛОГІКА ---

def get_events(filter_type: str):
    """
    filter_type: 'today', 'week', 'month', 'all'
    Повертає список подій, відсортований по даті.
    """
    events = load_events()
    if not events: return []

    # Функція сортування (Місяць, День)
    def sort_key(e):
        try:
            d, m = map(int, e['date'].split('.'))
            return m, d
        except: return 13, 32

    # Спочатку сортуємо все хронологічно
    events.sort(key=sort_key)

    if filter_type == "all":
        return events


    filtered = []
    today = datetime.now().date()

    for event in events:
        try:
            d, m = map(int, event['date'].split('.'))
        except: continue

        try:
            evt_date_this_year = datetime(today.year, m, d).date()
        except ValueError: continue 


        if evt_date_this_year < today:
             evt_date_next = datetime(today.year + 1, m, d).date()
             delta = (evt_date_next - today).days
        else:
             delta = (evt_date_this_year - today).days

        # Умови
        if filter_type == "today":
            if delta == 0: filtered.append(event)

        elif filter_type == "week":

            if 0 <= delta <= 7: filtered.append(event)

        elif filter_type == "month":

            if 0 <= delta <= 30: filtered.append(event)
    

    if filter_type in ['week', 'month']:
        def delta_sort(e):
            d, m = map(int, e['date'].split('.'))
            try:
                dt = datetime(today.year, m, d).date()
                if dt < today: dt = datetime(today.year + 1, m, d).date()
                return (dt - today).days
            except: return 999
        filtered.sort(key=delta_sort)

    return filtered

def add_new_event(date: str, name: str, raw_link: str = "-"):
    events = load_events()
    # Генеруємо ID
    new_id = max([e.get('id', 0) for e in events], default=0) + 1
    
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
    """Видалення за датою або назвою"""
    events = load_events()
    initial_count = len(events)
    query = query.lower().strip()
    
    new_events = []
    deleted_names = []
    
    for e in events:
        # Точний збіг дати АБО частковий збіг тексту
        if e['date'] == query or query in e['text'].lower():
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
        if e.get('id') == evt_id: return e
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
    events = load_events()
    lines = text_block.strip().split('\n')
    count = 0
    next_id = max([e.get('id', 0) for e in events], default=0) + 1

    for line in lines:
        parts = line.strip().split(maxsplit=1)
        if len(parts) < 2: continue
        
        date_str = parts[0]
        text_str = parts[1]
        
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
    txt = html.escape(event['text'])
    if event.get('link'):
        return f'<a href="{event["link"]}">{txt}</a>'
    return txt

def check_upcoming_events() -> str:
    """Формує текст для ранкового звіту"""
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
        except ValueError: continue
            
        if evt_date_this_year.date() < today.date():
             evt_date = datetime(today.year + 1, m, d)
        else:
             evt_date = evt_date_this_year
             
        delta = (evt_date.date() - today.date()).days
        link_text = decode_event_to_string(event)
        
        if delta == 0:
            list_today.append(link_text)
        elif delta == 1:
            list_tomorrow.append(link_text)
        elif 2 <= delta <= 7:
            list_week.append(f"{event['date']} - {link_text}")
            
    parts = []
    if list_today:
        parts.append(f"🔥 <b>СЬОГОДНІ:</b>\n" + "\n".join([f"• {x}" for x in list_today]))
    if list_tomorrow:
        parts.append(f"⚠️ <b>Завтра:</b>\n" + "\n".join([f"• {x}" for x in list_tomorrow]))
    if list_week:
        parts.append(f"👀 <b>На тижні:</b>\n" + "\n".join([f"• {x}" for x in list_week]))
        
    return "\n\n".join(parts) if parts else None

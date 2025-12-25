# services/calendar_api.py
import json
import os
import html
import base64
from datetime import datetime, timedelta
from config import OWNER_ID

JSON_FILE = "calendar.json"

# --- РОБОТА З ФАЙЛОМ (Base64) ---

def load_full_db():
    if not os.path.exists(JSON_FILE):
        return {}
    try:
        # Читаємо файл у бінарному режимі
        with open(JSON_FILE, "rb") as f:
            content = f.read()

        # Спроба 1: Пробуємо розкодувати Base64
        try:
            # Декодуємо Base64 -> отримуємо JSON рядок -> перетворюємо в словник
            json_str = base64.b64decode(content).decode('utf-8')
            data = json.loads(json_str)
        except Exception:
            # Спроба 2: Якщо впала помилка, значить файл ще "чистий" (не зашифрований)
            print("⚠️ Календар не зашифрований. Мігрую в Base64...")
            try:
                data = json.loads(content.decode('utf-8'))
                # Одразу зберігаємо його назад вже зашифрованим
                save_full_db(data)
            except:
                return {}

        # АВТО-МІГРАЦІЯ структури (список -> словник)
        if isinstance(data, list):
            new_db = {str(OWNER_ID): data}
            save_full_db(new_db)
            return new_db
        
        return data

    except Exception as e:
        print(f"❌ Error loading DB: {e}")
        return {}

def save_full_db(db_data):
    try:
        # 1. Перетворюємо словник у JSON-рядок
        json_str = json.dumps(db_data, ensure_ascii=False)
        # 2. Кодуємо цей рядок у Base64
        encrypted_bytes = base64.b64encode(json_str.encode('utf-8'))
        
        # 3. Записуємо набір байтів у файл
        with open(JSON_FILE, "wb") as f:
            f.write(encrypted_bytes)
    except Exception as e:
        print(f"❌ Error saving DB: {e}")

def get_user_events(user_id: int):
    db = load_full_db()
    return db.get(str(user_id), [])

def save_user_events(user_id: int, events: list):
    db = load_full_db()
    db[str(user_id)] = events
    save_full_db(db)

def get_events(user_id: int, filter_type: str):
    events = get_user_events(user_id)
    if not events: return []

    def sort_key(e):
        try:
            d, m = map(int, e['date'].split('.'))
            return m, d
        except: return 13, 32

    events.sort(key=sort_key)

    if filter_type == "all":
        return events

    filtered = []
    today = datetime.now().date()

    for event in events:
        try: d, m = map(int, event['date'].split('.'))
        except: continue

        try: evt_date_this_year = datetime(today.year, m, d).date()
        except ValueError: continue 

        if evt_date_this_year < today:
             evt_date_next = datetime(today.year + 1, m, d).date()
             delta = (evt_date_next - today).days
        else:
             delta = (evt_date_this_year - today).days

        if filter_type == "today" and delta == 0:
            filtered.append(event)
        elif filter_type == "week" and 0 <= delta <= 7:
            filtered.append(event)
        elif filter_type == "month" and 0 <= delta <= 30:
            filtered.append(event)
    
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

def add_new_event(user_id: int, date: str, name: str, raw_link: str = "-"):
    events = get_user_events(user_id)
    new_id = max([e.get('id', 0) for e in events], default=0) + 1
    
    link = None
    if raw_link and raw_link != "-":
        link = raw_link.strip()

    new_event = {
        "id": new_id,
        "date": date,
        "text": name,
        "link": link
    }
    events.append(new_event)
    save_user_events(user_id, events)
    return new_event

def delete_event(user_id: int, query: str) -> str:
    events = get_user_events(user_id)
    initial_count = len(events)
    query = query.lower().strip()
    
    new_events = []
    deleted_names = []
    
    for e in events:
        if e['date'] == query or query in e['text'].lower():
            deleted_names.append(f"{e['date']} ({e['text']})")
            continue
        new_events.append(e)
    
    if len(new_events) == initial_count:
        return "🤷‍♂️ Нічого не знайдено."
    
    save_user_events(user_id, new_events)
    return f"✅ Видалено {len(deleted_names)} подій:\n" + "\n".join(deleted_names)

def get_event_by_id(user_id: int, evt_id: int):
    events = get_user_events(user_id)
    for e in events:
        if e.get('id') == evt_id: return e
    return None

def update_event_text(user_id: int, evt_id: int, new_text: str):
    events = get_user_events(user_id)
    for e in events:
        if e.get('id') == evt_id:
            e['text'] = new_text
            save_user_events(user_id, events)
            return True
    return False

def mass_import_events(user_id: int, text_block: str):
    events = get_user_events(user_id)
    lines = text_block.strip().split('\n')
    count = 0
    next_id = max([e.get('id', 0) for e in events], default=0) + 1

    for line in lines:
        parts = line.strip().split(maxsplit=1)
        if len(parts) < 2 or "." not in parts[0]: continue
        events.append({"id": next_id, "date": parts[0], "text": parts[1], "link": None})
        next_id += 1
        count += 1
    save_user_events(user_id, events)
    return count

def decode_event_to_string(event):
    txt = html.escape(event['text'])
    if event.get('link'):
        return f'<a href="{event["link"]}">{txt}</a>'
    return txt

def check_upcoming_events(user_id: int = OWNER_ID) -> str:
    events = get_user_events(user_id)
    if not events: return None
    
    today = datetime.now()
    list_today, list_tomorrow, list_week = [], [], []
    
    for event in events:
        try: d, m = map(int, event['date'].split('.'))
        except: continue
        try: evt_date = datetime(today.year, m, d)
        except: continue
        
        if evt_date.date() < today.date():
             evt_date = datetime(today.year + 1, m, d)
             
        delta = (evt_date.date() - today.date()).days
        link_text = decode_event_to_string(event)
        
        if delta == 0: list_today.append(link_text)
        elif delta == 1: list_tomorrow.append(link_text)
        elif 2 <= delta <= 7: list_week.append(f"{event['date']} - {link_text}")
            
    parts = []
    if list_today: parts.append(f"🔥 <b>СЬОГОДНІ:</b>\n" + "\n".join([f"• {x}" for x in list_today]))
    if list_tomorrow: parts.append(f"⚠️ <b>Завтра:</b>\n" + "\n".join([f"• {x}" for x in list_tomorrow]))
    if list_week: parts.append(f"👀 <b>На тижні:</b>\n" + "\n".join([f"• {x}" for x in list_week]))
        
    return "\n\n".join(parts) if parts else None

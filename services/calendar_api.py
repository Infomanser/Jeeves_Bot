# services/calendar_api.py
import sqlite3
import html
from datetime import datetime
from config import OWNER_ID

DB_PATH = "data/jeeves_database.db"

def get_user_events(user_id: int):
    """Отримує всі події користувача з SQLite."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, date, text, link FROM calendar WHERE user_id = ?", 
                (user_id,)
            )
            rows = cursor.fetchall()
            
            events = []
            for row in rows:
                events.append({
                    "id": row[0],
                    "date": row[1],
                    "text": row[2],
                    "link": row[3]
                })
            return events
    except Exception as e:
        print(f"❌ DB Error (get_user_events): {e}")
        return []

def add_new_event(user_id: int, date: str, name: str, raw_link: str = "-"):
    """Додає подію в SQLite."""
    link = None
    if raw_link and raw_link != "-":
        link = raw_link.strip()
        
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO calendar (user_id, date, text, link) VALUES (?, ?, ?, ?)",
                (user_id, date, name, link)
            )
            conn.commit()
            return {"id": cursor.lastrowid, "date": date, "text": name, "link": link}
    except Exception as e:
        print(f"❌ DB Error (add_new_event): {e}")
        return None

def delete_event(user_id: int, query: str) -> str:
    """Видаляє події з SQLite за датою або текстом."""
    query = query.lower().strip()
    deleted_events = []
    
    all_events = get_user_events(user_id)
    ids_to_delete = []
    
    for e in all_events:
        if e['date'] == query or query in e['text'].lower():
            ids_to_delete.append(e['id'])
            deleted_events.append(f"{e['date']} ({e['text']})")
    
    if not ids_to_delete:
        return "🤷‍♂️ Нічого не знайдено."
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            placeholders = ', '.join('?' for _ in ids_to_delete)
            sql = f"DELETE FROM calendar WHERE id IN ({placeholders}) AND user_id = ?"
            params = ids_to_delete + [user_id]
            cursor.execute(sql, params)
            conn.commit()
            
        return f"✅ Видалено {len(deleted_events)} подій:\n" + "\n".join(deleted_events)
    except Exception as e:
        return f"❌ Помилка видалення: {e}"

def update_event_text(user_id: int, evt_id: int, new_text: str):
    """Оновлює текст події."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE calendar SET text = ? WHERE id = ? AND user_id = ?",
                (new_text, evt_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print(f"❌ DB Error (update): {e}")
        return False

def mass_import_events(user_id: int, text_block: str):
    """Масовий імпорт."""
    lines = text_block.strip().split('\n')
    count = 0
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            for line in lines:
                parts = line.strip().split(maxsplit=1)
                if len(parts) < 2 or "." not in parts[0]: continue
                
                cursor.execute(
                    "INSERT INTO calendar (user_id, date, text, link) VALUES (?, ?, ?, ?)",
                    (user_id, parts[0], parts[1], None)
                )
                count += 1
            conn.commit()
    except Exception as e:
        print(f"❌ DB Error (import): {e}")
    
    return count


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
        elif filter_type == "month" and 0 <= delta <= 31:
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

def get_event_by_id(user_id: int, evt_id: int):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, date, text, link FROM calendar WHERE id = ? AND user_id = ?", (evt_id, user_id))
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "date": row[1], "text": row[2], "link": row[3]}
    except: pass
    return None

def get_date_with_day(date_str: str) -> str:
    try:
        d, m = map(int, date_str.split('.'))
        current_year = datetime.now().year
        dt = datetime(current_year, m, d)
        days = ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота", "Неділя"]
        return f"{days[dt.weekday()]}, {date_str}"
    except:
        return date_str

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
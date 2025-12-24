# services/calendar_api.py
import json
import base64
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Шлях до файлу (піднімись на рівень вище від services)
BASE_DIR = Path(__file__).resolve().parent.parent
EVENTS_FILE = BASE_DIR / "calendar.json"

def _load_events() -> List[Dict]:
    if not EVENTS_FILE.exists(): return []
    try:
        with open(EVENTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Додаємо віртуальні ID для редагування
            for idx, item in enumerate(data):
                item['id'] = idx
            return data
    except: return []

def _save_events(events: List[Dict]):
    # Прибираємо ID перед записом
    clean_events = [{k: v for k, v in e.items() if k != 'id'} for e in events]
    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(clean_events, f, indent=4, ensure_ascii=False)

# --- READ ---
def get_events(filter_type: str = "all") -> List[Dict]:
    events = _load_events()
    if not events: return []
    
    # Сортування: ігноруємо рік, сортуємо по дню/місяцю
    events.sort(key=lambda x: datetime.strptime(x['date'], "%d.%m"))

    if filter_type == "all": return events

    now = datetime.now()
    filtered = []
    
    for event in events:
        try:
            # Створюємо дату поточного року
            evt_date = datetime.strptime(f"{event['date']}.{now.year}", "%d.%m.%Y")
            delta = (evt_date - now).days + 1 
            
            if filter_type == "today" and delta == 0: filtered.append(event)
            elif filter_type == "week" and 0 <= delta <= 7: filtered.append(event)
            elif filter_type == "month" and 0 <= delta <= 30: filtered.append(event)
        except: continue
        
    return filtered

def get_event_by_id(evt_id: int) -> Optional[Dict]:
    events = _load_events()
    if 0 <= evt_id < len(events):
        return events[evt_id]
    return None

# --- WRITE ---
def update_event_text(evt_id: int, new_text: str) -> bool:
    events = _load_events()
    if 0 <= evt_id < len(events):
        events[evt_id]['text'] = new_text
        _save_events(events)
        return True
    return False

def mass_import_events(text_block: str) -> int:
    events = _load_events()
    count = 0
    for line in text_block.strip().split('\n'):
        parts = line.strip().split(maxsplit=1)
        if len(parts) == 2:
            date_str, name = parts
            if "." in date_str: # Мінімальна валідація
                events.append({"date": date_str, "text": name})
                count += 1
    if count > 0: _save_events(events)
    return count

def add_new_event(date: str, name: str, raw_link: str = None) -> Dict:
    new_event = {"date": date, "text": name}
    if raw_link and raw_link.lower() not in ["-", "ні", "no"]:
        # Обробка лінків
        final = raw_link.strip()
        digits = ''.join(filter(str.isdigit, final))
        if "viber" in final: final = f"https://viber.click/{digits}"
        elif "wa.me" in final: final = f"https://wa.me/{digits}"
        elif final.startswith("@"): final = f"https://t.me/{final[1:]}"
        
        b64 = base64.b64encode(final.encode()).decode()
        new_event['link'] = b64
        
    events = _load_events()
    events.append(new_event)
    _save_events(events)
    return new_event

# --- HELPERS ---
def decode_event_to_string(event: Dict) -> str:
    text = event['text']
    if event.get('link'):
        try:
            url = base64.b64decode(event['link']).decode()
            icon = "🌐"
            if "t.me" in url: icon = "✈️"
            elif "viber" in url: icon = "🟣"
            return f"<a href='{url}'>{text}</a> {icon}"
        except: pass
    return text

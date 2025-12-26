import json
import sqlite3
from services.db_manager import get_connection

def migrate_calendar():

    json_path = "calendar.json"
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            old_data = json.load(f)
        
        conn = get_connection()
        cursor = conn.cursor()
        
        count = 0
        for user_id, events in old_data.items():
            for event in events:
                cursor.execute('''
                    INSERT INTO calendar (user_id, event_date, event_text, link)
                    VALUES (?, ?, ?, ?)
                ''', (int(user_id), event['date'], event['text'], event.get('link')))
                count += 1
        
        conn.commit()
        conn.close()
        print(f"✅ Міграція завершена! Перенесено {count} записів.")
    except FileNotFoundError:
        print("❌ Файл calendar.json не знайдено.")
    except Exception as e:
        print(f"❌ Помилка міграції: {e}")

if __name__ == "__main__":
    migrate_calendar()

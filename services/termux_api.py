# services/termux_api.py
import subprocess
import json
import shutil
import html

def run_command(cmd_list):
    """Універсальна запускалка команд"""
    try:
        result = subprocess.run(cmd_list, capture_output=True, text=True, timeout=10)
        return result.stdout.strip()
    except Exception as e:
        return None

def get_uptime() -> str:
    up = run_command(['uptime', '-p'])
    return up.replace("up ", "") if up else "Невідомо"

def get_battery_info() -> str:
    try:
        raw = run_command(['termux-battery-status'])
        if raw:
            data = json.loads(raw)
            status = data.get('status', 'UNKNOWN')
            
            # Переклад статусів
            status_map = {
                'CHARGING': '🔌 Заряджається',
                'DISCHARGING': '🔋 Розряджається',
                'FULL': '✅ Повна',
                'NOT_CHARGING': '🚫 Не заряджається'
            }
            status_text = status_map.get(status, status)
            return f"{data.get('percentage', 0)}% ({status_text}), {data.get('temperature', 0)}°C"
    except: pass
    return "Дані недоступні"

def get_ram_usage() -> str:
    try:
        # free -m повертає таблицю. Парсимо другий рядок.
        raw = run_command(['free', '-m'])
        if raw:
            line = raw.splitlines()[1].split()
            # line[1]=Total, line[2]=Used
            total = int(line[1])
            used = int(line[2])
            return f"{used/1024:.2f} / {total/1024:.2f} GB"
    except: pass
    return "RAM Error"

def get_storage_info() -> str:
    try:
        total, used, free = shutil.disk_usage(".")
        percent = (used / total) * 100
        f_percent = (free / total) * 100
        gb = 1024**3
        return (f"📦 Всього: {total/gb:.2f} GB\n"
                f"🚫 Зайнято: {used/gb:.2f} GB ({percent:.1f}%)\n"
                f"✅ Вільно:  {free/gb:.2f} GB ({f_percent:.1f}%)")
    except: return "Storage Error"

def get_pm2_list() -> str:
    # --no-color важливо, щоб не було зайвих символів у Telegram
    out = run_command(['pm2', 'list', '--no-color'])
    return out if out else "PM2 не відповідає"

def restart_pm2_service(name: str) -> bool:
    try:
        subprocess.run(['pm2', 'restart', name], check=True)
        return True
    except:
        return False

# --- Hardware Control ---

def torch_control(state: str):
    """state: 'on' or 'off'"""
    run_command(['termux-torch', state])

def speak_text(text: str):
    subprocess.Popen(['termux-tts-speak', text])

def get_full_system_report() -> str:
    """Збирає все докупи для команди /status"""
    return (
        f"📊 <b>System Status:</b>\n"
        f"⏱ <b>Аптайм:</b> {get_uptime()}\n"
        f"🔋 <b>Батарея:</b> {get_battery_info()}\n"
        f"💾 <b>RAM:</b> {get_ram_usage()}\n\n"
        f"<pre>{html.escape(get_pm2_list())}</pre>"
    )

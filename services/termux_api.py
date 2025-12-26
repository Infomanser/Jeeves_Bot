import subprocess
import json
import time
from datetime import datetime

# --- ДОПОМІЖНІ ФУНКЦІЇ ---

def run_command(command):
    """Запускає команду в терміналі і повертає результат"""
    try:
        return subprocess.check_output(command, encoding='utf-8').strip()
    except Exception as e:
        return ""

def get_bar(percent, length=10):
    """Малює прогрес-бар [■■■□□]"""
    try:
        percent = float(percent)
        filled = int(length * percent / 100)
        return "■" * filled + "□" * (length - filled)
    except:
        return "□" * length

def ukrainian_uptime(uptime_str):
    translations = {
        "up": "",
        "weeks": "тиж", "week": "тижд",
        "days": "дн", "day": "дн",
        "hours": "год", "hour": "год",
        "minutes": "хв", "minute": "хв",
        ",": ""
    }
    for old, new in translations.items():
        uptime_str = uptime_str.replace(old, new)
    return uptime_str.strip()

def format_pm2_uptime(uptime_ms):
    diff = int(time.time() * 1000) - uptime_ms
    seconds = diff // 1000
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    if days > 0: return f"{days}д {hours}г"
    elif hours > 0: return f"{hours}г {minutes}хв"
    else: return f"{minutes}хв"

# --- 🔦 ХАРДВЕРНІ ФУНКЦІЇ (Ми їх повернули!) ---

def torch(state: str):
    """Керування ліхтариком (on/off)"""
    try:
        # termux-torch on / termux-torch off
        subprocess.Popen(["termux-torch", state])
    except Exception as e:
        print(f"Error torch: {e}")

def tts_speak(text: str):
    """Озвучка тексту (Text-to-Speech)"""
    try:
        # Використовуємо Popen, щоб не блокувати бота поки він говорить
        subprocess.Popen(["termux-tts-speak", text])
    except Exception as e:
        print(f"Error TTS: {e}")

# --- ЗВІТИ ТА PM2 ---

def get_pm2_stats():
    try:
        result = subprocess.check_output(["pm2", "jlist"], encoding='utf-8')
        processes = json.loads(result)
        if not processes: return "Процеси відсутні."

        report = "📊 <b>Процеси PM2:</b>\n<pre>"
        report += f"{'ID':<2} {'Назва':<10} {'Час':<6} {'Стан':<2} {'ОЗП':<5}\n"
        report += "─"*30 + "\n"

        for proc in processes:
            pm_id = proc.get('pm_id', 0)
            name = proc.get('name', 'N/A')[:10]
            status_raw = proc['pm2_env'].get('status', 'stopped')
            status = "🟢" if status_raw == 'online' else ("🔴" if status_raw == 'errored' else "⚪️")
            uptime_ms = proc['pm2_env'].get('pm_uptime', 0)
            uptime_str = format_pm2_uptime(uptime_ms) if status_raw == 'online' else "-"
            mem_bytes = proc.get('monit', {}).get('memory', 0)
            mem_mb = f"{int(mem_bytes / 1024 / 1024)}M"
            report += f"{pm_id:<2} {name:<10} {uptime_str:<6} {status:<2} {mem_mb:<5}\n"
        
        report += "</pre>"
        return report
    except Exception as e:
        return f"⚠️ Помилка PM2: {str(e)}"

def get_full_system_report() -> str:
    current_time = datetime.now().strftime("%H:%M")
    raw_uptime = run_command(["uptime", "-p"])
    uptime_ua = ukrainian_uptime(raw_uptime.replace("up ", ""))
    header = f"🕰 <b>System ({current_time}):</b>\n⏱️ В мережі: {uptime_ua}"

    # Батарея з тайм-аутом
    try:
        result = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=2)
        bat_data = json.loads(result.stdout)
        p = bat_data.get("percentage", 0)
        temp = bat_data.get("temperature", 0)
        st = bat_data.get("status", "Unknown").upper()
        st_ua = "заряджається" if "CHARGING" in st else ("автономно" if "DISCHARGING" in st else "повний")
        icon = "⚡️" if "CHARGING" in st else ("🪫" if p < 20 else "🔋")
        battery_info = f"🔋 Акум: {icon} {p}% ({st_ua}, {temp}°C)"
    except subprocess.TimeoutExpired:
        battery_info = "🔋 Акум: ⏳ (API не відповідає)"
    except:
        battery_info = "🔋 Акум: Невідомо"

    # RAM
    try:
        ram_out = run_command(["free", "-m"])
        lines = ram_out.split('\n')
        ram_info = "🧠 ОЗП: n/a"
        for line in lines:
            if "Mem:" in line:
                p_ram = line.split()
                used, total = int(p_ram[2]), int(p_ram[1])
                ram_bar = get_bar((used/total)*100)
                ram_info = f"🧠 ОЗП: <code>[{ram_bar}]</code> {used}М / {total}М"
                break
    except: ram_info = "🧠 ОЗП: помилка"

    # Диск
    try:
        output = run_command(["df", "-h", "/data"])
        parts = output.strip().split('\n')[1].split()
        disk_p = parts[4].replace('%', '')
        disk_bar = get_bar(disk_p)
        disk_info = f"💾 Пам'ять: <code>[{disk_bar}]</code> {parts[2]} / {parts[1]} ({disk_p}%)"
    except: disk_info = "💾 Пам'ять: n/a"

    return f"{header}\n{battery_info}\n{ram_info}\n{disk_info}\n\n{get_pm2_stats()}"
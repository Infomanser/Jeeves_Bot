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
    """Перекладає англійський uptime (up 2 days, 4 hours) на людську мову"""
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
    """Перетворює timestamp запуску PM2 в читабельний рядок"""
    diff = int(time.time() * 1000) - uptime_ms
    seconds = diff // 1000
    
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    
    if days > 0:
        return f"{days}д {hours}г"
    elif hours > 0:
        return f"{hours}г {minutes}хв"
    else:
        return f"{minutes}хв"

# --- ОСНОВНА ЛОГІКА PM2 ---

def get_pm2_stats():
    try:
        result = subprocess.check_output(["pm2", "jlist"], encoding='utf-8')
        processes = json.loads(result)
        
        if not processes:
            return "Процеси відсутні."

        # Шапка таблиці
        report = "📊 <b>Процеси PM2:</b>\n<pre>"
        report += f"{'ID':<2} {'Назва':<10} {'Час':<6} {'Стан':<2} {'ОЗП':<5}\n"
        report += "─"*30 + "\n"

        for proc in processes:
            pm_id = proc.get('pm_id', 0)
            name = proc.get('name', 'N/A')[:10]
            
            # Статус
            status_raw = proc['pm2_env'].get('status', 'stopped')
            if status_raw == 'online':
                status = "🟢"
            elif status_raw == 'stopping':
                status = "🟡"
            elif status_raw == 'errored':
                status = "🔴"
            else:
                status = "⚪️"

            # Аптайм
            uptime_ms = proc['pm2_env'].get('pm_uptime', 0)
            uptime_str = format_pm2_uptime(uptime_ms) if status_raw == 'online' else "-"

            # Пам'ять
            mem_bytes = proc.get('monit', {}).get('memory', 0)
            mem_mb = f"{int(mem_bytes / 1024 / 1024)}M"

            report += f"{pm_id:<2} {name:<10} {uptime_str:<6} {status:<2} {mem_mb:<5}\n"
        
        report += "</pre>"
        return report

    except Exception as e:
        return f"⚠️ Помилка PM2: {str(e)}"

# --- ЗБІР ПОВНОГО ЗВІТУ ---

def get_full_system_report() -> str:
    # 1. Заголовок і Час роботи
    current_time = datetime.now().strftime("%H:%M")
    raw_uptime = run_command(["uptime", "-p"])
    uptime_ua = ukrainian_uptime(raw_uptime.replace("up ", ""))
    
    header = f"🕰 <b>System ({current_time}):</b>\n⏱️ В мережі: {uptime_ua}"

    # 2. Батарея
    try:
        bat_raw = run_command(["termux-battery-status"])
        bat_data = json.loads(bat_raw)
        p = bat_data.get("percentage", 0)
        temp = bat_data.get("temperature", 0)
        st = bat_data.get("status", "Unknown").upper()
        
        st_ua = "автономно"
        if "CHARGING" in st: st_ua = "заряджається"
        elif "DISCHARGING" in st: st_ua = "розряджається"
        elif "FULL" in st: st_ua = "повний"
        
        icon = "⚡️" if "CHARGING" in st else ("🪫" if p < 20 else "🔋")
        battery_info = f"🔋 Акум: {icon} {p}% ({st_ua}, {temp}°C)"
    except:
        battery_info = "🔋 Акум: Невідомо"

    # 3. Пам'ять (RAM)
    try:
        ram_out = run_command(["free", "-m"])
        lines = ram_out.split('\n')
        ram_info = "🧠 ОЗП: n/a"
        for line in lines:
            if "Mem:" in line:
                p_ram = line.split()
                total, used = int(p_ram[1]), int(p_ram[2])
                if total > 0:
                    ram_p = (used / total) * 100
                    ram_bar = get_bar(ram_p)
                    ram_info = f"🧠 ОЗП: <code>[{ram_bar}]</code> {used}М / {total}М"
                break
    except:
        ram_info = "🧠 ОЗП: Помилка"

    # 4. Диск
    try:
        output = run_command(["df", "-h", "/data"])
        lines = output.strip().split('\n')
        parts = lines[1].split()
        disk_used_val = parts[2]
        disk_total_val = parts[1]
        disk_p_str = parts[4].replace('%', '')
        disk_bar = get_bar(disk_p_str)
        disk_info = f"💾 Пам'ять: <code>[{disk_bar}]</code> {disk_used_val} / {disk_total_val} ({disk_p_str}%)"
    except:
        disk_info = "💾 Пам'ять: n/a"

    # 5. PM2 (наша нова функція)
    pm2_report = get_pm2_stats()

    return f"{header}\n{battery_info}\n{ram_info}\n{disk_info}\n\n{pm2_report}"
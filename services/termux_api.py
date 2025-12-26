# services/termux_api.py
import subprocess
import json
import shutil
import sqlite3
from datetime import datetime

def run_command(command: list) -> str:
    """Виконує shell команду і повертає результат текстом"""
    try:
        result = subprocess.check_output(command, stderr=subprocess.STDOUT)
        return result.decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.output.decode('utf-8')}"
    except Exception as e:
        return f"Error: {str(e)}"

# --- PM2 ---
def restart_pm2_service(service_name: str) -> bool:
    try:
        subprocess.run(
            ["pm2", "restart", service_name, "--update-env"], 
            check=True, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False

def get_pm2_list_raw() -> str:
    """Повертає таблицю процесів (як в консолі)"""
    try:
        # Лiтеру 'G' прибрано тут
        return run_command(["pm2", "list", "--no-color"])
    except:
        return "Не вдалося отримати список PM2"

# --- Hardware Control ---
def torch_control(state: str):
    subprocess.run(["termux-torch", state], check=False)

def speak_text(text: str):
    subprocess.run(["termux-tts-speak", text], check=False)

# --- Info Helpers ---
def get_bar(percent, length=10):
    """Створює прогрес-бар [■■■□□]"""
    try:
        percent = float(str(percent).replace('%', ''))
        percent = max(0, min(100, percent))
        filled = int(length * percent / 100)
        return "■" * filled + "□" * (length - filled)
    except:
        return "□" * length

def ukrainian_uptime(uptime_str):
    """Перекладає '6 days, 23 hours' на українську"""
    res = uptime_str.replace("days", "дн").replace("day", "дн")
    res = res.replace("hours", "г").replace("hour", "г")
    res = res.replace("minutes", "хв").replace("minute", "хв")
    return res

# --- Main Report ---
def get_full_system_report() -> str:
    """Збирає красивий українізований звіт"""
    
    # 1. Battery Info
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
        bat_info = f"{icon} {p}% ({st_ua}, {temp}°C)"
    except:
        bat_info = "🔋 Невідомо"

    # 2. Storage Info + Bar
    try:
        output = run_command(["df", "-h", "/data"])
        lines = output.strip().split('\n')
        parts = lines[1].split()
        disk_used_val = parts[2]
        disk_total_val = parts[1]
        disk_p_str = parts[4].replace('%', '')
        disk_bar = get_bar(disk_p_str)
        disk_info = f"<code>[{disk_bar}]</code> {disk_used_val} / {disk_total_val} ({disk_p_str}%)"
    except:
        disk_info = "💾 n/a"

    # 3. RAM Info + Bar
    try:
        ram_out = run_command(["free", "-m"])
        lines = ram_out.split('\n')
        ram_display = "n/a"
        for line in lines:
            if "Mem:" in line:
                p_ram = line.split()
                total, used = int(p_ram[1]), int(p_ram[2])
                ram_p = (used / total) * 100
                ram_bar = get_bar(ram_p)
                ram_display = f"<code>[{ram_bar}]</code> {used}М / {total}М"
                break
    except:
        ram_display = "🧠 n/a"

    # 4. Uptime & PM2
    uptime = ukrainian_uptime(run_command(["uptime", "-p"]).replace("up ", ""))
    pm2_table = get_pm2_list_raw()
    current_time = datetime.now().strftime("%H:%M")

    return (
        f"🕰 <b>Системний звіт ({current_time}):</b>\n\n"
        f"⏱ <b>В мережі:</b> {uptime}\n"
        f"🔋 <b>Акум:</b> {bat_info}\n"
        f"🧠 <b>ОЗП:</b> {ram_display}\n"
        f"💾 <b>Пам'ять:</b> {disk_info}\n\n"
        f"📊 <b>Процеси PM2:</b>\n"
        f"<pre>{pm2_table}</pre>"
    )
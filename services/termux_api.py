# services/termux_api.py
import subprocess
import json
import shutil

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
        # --no-color, щоб прибрати ANSI коди, які ламають вигляд в TG
        return run_command(["pm2", "list", "--no-color"])
    except:
        return "Не вдалося отримати список PM2"

# --- Hardware Control ---
def torch_control(state: str):
    subprocess.run(["termux-torch", state], check=False)

def speak_text(text: str):
    subprocess.run(["termux-tts-speak", text], check=False)

# --- Info ---
def get_storage_info() -> str:
    """Повертає інфо про диск (саме про користувацькі дані)"""
    # На Android корінь / завжди 100%, тому дивимось /data
    try:
        output = run_command(["df", "-h", "/data"])
        # output зазвичай:
        # Filesystem      Size  Used Avail Use% Mounted on
        # /dev/...        100G   50G   50G  50% /data
        lines = output.strip().split('\n')
        if len(lines) >= 2:
            # Розбиваємо другий рядок на колонки
            parts = lines[1].split()
            # Формуємо красивий рядок: 50G / 100G (50%)
            # parts[1]=Size, parts[2]=Used, parts[4]=Use%
            return f"{parts[2]} / {parts[1]} ({parts[4]})"
        return output
    except:
        return "Unknown"

def get_battery_info() -> str:
    try:
        output = run_command(["termux-battery-status"])
        data = json.loads(output)
        percentage = data.get("percentage", 0)
        status = data.get("status", "Unknown")
        
        icon = "🔋"
        if status == "Charging": icon = "⚡️"
        elif percentage < 20: icon = "🪫"
        
        temp = data.get("temperature", 0)
        
        return f"{icon} {percentage}% ({status}), {temp}°C"
    except:
        return "🔋 Невідомо"

def get_uptime() -> str:
    return run_command(["uptime", "-p"]).replace("up ", "")

def get_full_system_report() -> str:
    """Збирає все докупи"""
    bat = get_battery_info()
    disk = get_storage_info()
    uptime = get_uptime()
    pm2_table = get_pm2_list_raw()
    
    # RAM Parse
    try:
        # free -h --si (щоб були гігабайти, а не гібібайти, якщо підтримується)
        # або просто free -m для точності
        ram_out = run_command(["free", "-h"])
        lines = ram_out.split('\n')
        ram_info = "n/a"
        for line in lines:
            if "Mem:" in line:
                parts = line.split()
                # Total=1, Used=2
                ram_info = f"{parts[2]} / {parts[1]}"
                break
    except:
        ram_info = "n/a"

    # Формуємо звіт
    # pm2_table загортаємо в <pre>, щоб не поїхали стовпчики
    return (
        f"🕰 <b>System Status:</b>\n"
        f"⏱ <b>Uptime:</b> {uptime}\n"
        f"🔋 <b>Bat:</b> {bat}\n"
        f"🧠 <b>RAM:</b> {ram_info}\n"
        f"💾 <b>Disk (/data):</b> {disk}\n\n"
        f"<pre>{pm2_table}</pre>"
    )

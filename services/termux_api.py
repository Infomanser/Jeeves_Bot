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
    """Перезавантажує сервіс через PM2"""
    try:
        # --update-env важливо, якщо змінювались змінні середовища
        subprocess.run(
            ["pm2", "restart", service_name, "--update-env"], 
            check=True, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False

# --- Hardware Control ---
def torch_control(state: str):
    """state: 'on' або 'off'"""
    # termux-torch on / termux-torch off
    subprocess.run(["termux-torch", state], check=False)

def speak_text(text: str):
    """Озвучує текст через TTS двигун Android"""
    # -r rate (швидкість), -p pitch (тон) - можна налаштувати
    subprocess.run(["termux-tts-speak", text], check=False)

# --- Info ---
def get_storage_info() -> str:
    """Повертає інфо про диск"""
    # df -h /storage/emulated (або просто /data)
    try:
        # Для читабельності беремо root
        output = run_command(["df", "-h", "/"])
        # Зазвичай це два рядки, беремо другий
        lines = output.split('\n')
        if len(lines) >= 2:
            return lines[1] # Size Used Avail Use% Mounted
        return output
    except:
        return "Не вдалося отримати дані диска."

def get_battery_info() -> str:
    """Повертає статус батареї через Termux API"""
    try:
        # termux-battery-status повертає JSON
        output = run_command(["termux-battery-status"])
        data = json.loads(output)
        percentage = data.get("percentage", 0)
        status = data.get("status", "Unknown") # Charging, Discharging, Full
        plugged = data.get("plugged", "UNPLUGGED")
        
        icon = "🔋"
        if status == "Charging": icon = "⚡️"
        
        return f"{icon} {percentage}% ({status})"
    except:
        return "🔋 Невідомо (Termux API error)"

def get_uptime() -> str:
    """Час роботи пристрою"""
    # uptime -p виводить 'up 2 days, 4 hours'
    return run_command(["uptime", "-p"]).replace("up ", "")

def get_full_system_report() -> str:
    """Збирає все докупи для команди Статус"""
    bat = get_battery_info()
    disk = get_storage_info()
    uptime = get_uptime()
    
    # RAM через free -h
    try:
        ram_out = run_command(["free", "-h"])
        # Розбір виводу free (шукаємо рядок Mem:)
        ram_lines = ram_out.split('\n')
        ram_info = "RAM data error"
        for line in ram_lines:
            if "Mem:" in line:
                # Mem: Total Used Free ...
                parts = line.split()
                # parts[1]=Total, parts[2]=Used, parts[6]=Available (на Linux)
                # Termux може відрізнятись, тому просто повернемо рядок
                ram_info = f"{parts[2]}/{parts[1]} (Used/Total)"
                break
    except:
        ram_info = "n/a"

    return (
        f"🤖 <b>System Report</b>\n"
        f"⏱ <b>Uptime:</b> {uptime}\n"
        f"🔋 <b>Battery:</b> {bat}\n"
        f"🧠 <b>RAM:</b> {ram_info}\n"
        f"💾 <b>Disk (/):</b> {disk}"
    )

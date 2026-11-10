import json
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from supabase import create_client

# =========================
# НАСТРОЙКИ
# =========================

SUPABASE_URL = "https://nzpfbvrbwmxhhpajgyjj.supabase.co"
SUPABASE_KEY = "sb_publishable_htg_8lgoGKWP7Dx7eVlhDg_eLnr3Y10"

GROWATT_API = "https://openapi.growatt.com"
GROWATT_TOKEN = "kh3w9600ko1723x05n6146290m44492l"

# Вставьте сюда токен ВАШЕГО Telegram-бота и ВАШ Chat ID
TELEGRAM_BOT_TOKEN = "9031052092:AAGLoZiGVFSRLpayP4H4ifNkEc7ufF879wA"

TELEGRAM_CHAT_IDS = [
    "414695641"
]

DEVICE_TYPE = "storage"
DEVICE_SN = "UYN9G5N141"  # Серийник вашего инвертора

KYIV = ZoneInfo("Europe/Kyiv")
STATE_FILE = Path("power_state.json")
REPORT_INTERVAL = 60  # Обычный отчёт один раз в час

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# ВРЕМЯ
# =========================

def now_kyiv():
    return datetime.now(KYIV)

# =========================
# TELEGRAM
# =========================

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    for chat_id in TELEGRAM_CHAT_IDS:
        try:
            response = requests.post(
                url,
                data={
                    "chat_id": chat_id,
                    "text": message
                },
                timeout=20
            )
            if not response.ok:
                print(f"Ошибка Telegram для {chat_id}: {response.text}")
        except Exception as e:
            print(f"Ошибка отправки в Telegram для {chat_id}: {e}")

# =========================
# GROWATT
# =========================

def get_growatt_data():
    url = f"{GROWATT_API}/v4/new-api/queryLastData"
    headers = {
        "token": GROWATT_TOKEN,
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.post(
        url,
        headers=headers,
        data={
            "deviceType": DEVICE_TYPE,
            "deviceSn": DEVICE_SN
        },
        timeout=30
    )
    response.raise_for_status()
    result = response.json()
    
    if str(result.get("code")) != "0":
        raise Exception(f"Growatt API error: {result}")
        
    devices = result.get("data", {}).get("storage", [])
    device = next(
        (item for item in devices if item.get("serialNum") == DEVICE_SN),
        None
    )
    
    if device is None:
        if devices:
            device = devices[0]
        else:
            raise Exception("Устройство Growatt не найдено")
            
    return device

# =========================
# ОПРЕДЕЛЕНИЕ СЕТИ
# =========================

def detect_grid(data):
    try:
        grid_voltage = float(data.get("vGrid", 0))
    except (TypeError, ValueError):
        return None

    if grid_voltage >= 100:
        return True
    if grid_voltage < 50:
        return False
    return None

# =========================
# ФОРМАТИРОВАНИЕ
# =========================

def watts(value):
    if value is None:
        return "нет данных"
    try:
        return f"{float(value):.0f} Вт"
    except (TypeError, ValueError):
        return "нет данных"

def percent(value):
    if value is None:
        return "нет данных"
    try:
        return f"{float(value):.0f}%"
    except (TypeError, ValueError):
        return "нет данных"

def voltage(value):
    if value is None:
        return "нет данных"
    try:
        return f"{float(value):.1f} В"
    except (TypeError, ValueError):
        return "нет данных"

# =========================
# СОСТОЯНИЕ
# =========================

def load_state():
    if not STATE_FILE.exists():
        return {}
    try:
        with STATE_FILE.open("r", encoding="utf-8") as file:
            state = json.load(file)
        return state if isinstance(state, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}

def save_state(state):
    with STATE_FILE.open("w", encoding="utf-8") as file:
        json.dump(state, file, ensure_ascii=False, indent=2)

def format_duration(start_time, end_time):
    duration = end_time - start_time
    total_seconds = max(0, int(duration.total_seconds()))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours > 0:
        return f"{hours} год {minutes} хв"
    if minutes > 0:
        return f"{minutes} хв {seconds} сек"
    return f"{seconds} сек"

# =========================
# ОТЧЁТ И СИНХРОНИЗАЦИЯ С SUPABASE
# =========================

def make_report(data, grid):
    apartment_power = data.get("outPutPower")
    inverter_power = data.get("pBat")
    battery_soc = data.get("bmsSoc")
    output_voltage = data.get("outPutVolt")
    grid_voltage = data.get("vGrid")
    
    if grid:
        grid_text = "🟢 Мережа відновлена. Живлення від міста ⚡"
        battery_mode = "ПИТАНИЕ ОТ СЕТИ ⚡"
    else:
        grid_text = "🔴 Світло зникло! Перемикання на резерв (АКБ) 🔋"
        battery_mode = "РАБОТА ОТ РЕЗЕРВНОГО ПИТАНИЯ 🔋"

    return (
        "🗣️ **МОНИТОРИНГ GROWATT**\n\n"
        f"{grid_text}\n\n"
        f"🏠 Потребление квартиры: {watts(apartment_power)}\n"
        f"🔋 Заряд батареи: {percent(battery_soc)}\n"
        f"⚡ Отдача инвертора: {watts(inverter_power)}\n"
        f"🏡 Напряжение выхода: {voltage(output_voltage)}\n"
        f"⚡ Напряжение сети: {voltage(grid_voltage)}\n\n"
        f"🕒 {now_kyiv().strftime('%d.%m.%Y %H:%M:%S')}"
    )

def push_to_supabase(grid, data):
    try:
        grid_status = bool(grid)
        battery_soc = int(float(data.get("bmsSoc", 0) or 0))
        load_power = int(float(data.get("outPutPower", 0) or 0))
        grid_voltage = float(data.get("vGrid", 0) or 0)
        discharge_power = round(load_power / 1000, 2) # в кВт для нового интерфейса
        
        supabase.table("power_logs").insert({
            "grid_status": grid_status,
            "battery_soc": battery_soc,
            "load_power": load_power,
            "grid_voltage": grid_voltage,
            "discharge_power": discharge_power
        }).execute()
        print("✅ Данные успешно записаны в Supabase.")
    except Exception as e:
        print(f"⚠️ Ошибка записи в Supabase: {e}")

# =========================
# ОСНОВНАЯ ПРОВЕРКА
# =========================

def check_power():
    current_time = now_kyiv()
    print("===================================")
    print("Проверка Growatt:", current_time)

    state = load_state()
    data = get_growatt_data()
    print("Данные Growatt получены.")

    grid = detect_grid(data)
    if grid is None:
        print("Не удалось определить состояние городской сети.")
        return

    print("Городская сеть:", grid)

    # Записываем свежие данные в Supabase при каждом успешном опросе
    push_to_supabase(grid, data)

    previous = state.get("power")
    event = None

    if previous is True and grid is False:
        state["power_off_time"] = current_time.isoformat()
        event = (
            "🔴 **СВІТЛО ЗНИКЛО!** ❌⚡\n\n"
            f"🕒 Час зникнення: {current_time.strftime('%d.%m.%Y %H:%M:%S')}"
        )
        print("🔴 СВІТЛО ЗНИКЛО:", current_time)

    elif previous is False and grid is True:
        power_off_time = state.get("power_off_time")
        if power_off_time:
            try:
                off_time = datetime.fromisoformat(power_off_time)
                duration = format_duration(off_time, current_time)
                event = (
                    "🟢 **СВІТЛО З'ЯВИЛОСЯ!** 💡⚡\n\n"
                    f"🕒 Зникло: {off_time.strftime('%d.%m.%Y %H:%M:%S')}\n"
                    f"🕒 З'явилося: {current_time.strftime('%d.%m.%Y %H:%M:%S')}\n\n"
                    f"⏱ Не було світла: {duration}"
                )
            except (ValueError, TypeError):
                event = (
                    "🟢 **СВІТЛО З'ЯВИЛОСЯ!** 💡⚡\n\n"
                    f"🕒 Час появи: {current_time.strftime('%d.%m.%Y %H:%M:%S')}"
                )
        else:
            event = (
                "🟢 **СВІТЛО З'ЯВИЛОСЯ!** 💡⚡\n\n"
                f"🕒 Час появи: {current_time.strftime('%d.%m.%Y %H:%M:%S')}"
            )
        state.pop("power_off_time", None)
        print("🟢 СВІТЛО З'ЯВИЛОСЯ:", current_time)

    last_report = state.get("last_report")
    report_due = False

    if not last_report:
        report_due = True
    else:
        try:
            last_report_time = datetime.fromisoformat(last_report)
            if last_report_time.tzinfo is None:
                last_report_time = last_report_time.replace(tzinfo=KYIV)
            if current_time - last_report_time >= timedelta(minutes=REPORT_INTERVAL):
                report_due = True
        except (ValueError, TypeError):
            report_due = True

    if event or report_due:
        message = make_report(data, grid)
        if event:
            message = event + "\n\n" + message
        send_telegram(message)
        state["last_report"] = current_time.isoformat()
        print("Telegram: сообщение отправлено.")

    state["power"] = grid
    state["updated"] = current_time.isoformat()
    save_state(state)

    print("Потребление квартиры:", data.get("outPutPower"))
    print("Отдача инвертора:", data.get("pBat"))
    print("Заряд батареи:", data.get("bmsSoc"))
    print("===================================")

# =========================
# ЗАПУСК
# =========================

if __name__ == "__main__":
    try:
        check_power()
    except Exception as error:
        print("ОШИБКА:", error)
        try:
            send_telegram(
                "⚠️ ОШИБКА ПРОВЕРКИ GROWATT\n\n"
                f"{error}"
            )
        except Exception as telegram_error:
            print("Ошибка Telegram:", telegram_error)
        raise

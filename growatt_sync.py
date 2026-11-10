import requests
import hashlib
from supabase import create_client

SUPABASE_URL = "https://nzpfbvrbwmxhhpajgyjj.supabase.co"
SUPABASE_KEY = "sb_publishable_htg_8lgoGKWP7Dx7eVlhDg_eLnr3Y10"

GROWATT_USER = "Viachealav"
GROWATT_PASS = "Iloveyara2552"
DATALOGGER_SN = "HAQ1G5H24S"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_md5(password):
    return hashlib.md5(password.encode('utf-8')).hexdigest()

def fetch_and_push():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
        "Content-Type": "application/x-www-form-urlencoded"
    })

    # Список возможных серверов Growatt (в зависимости от региона)
    servers = [
        "https://server.growatt.com",
        "https://server-api.growatt.com"
    ]

    login_data = None
    active_server = None

    for server in servers:
        login_url = f"{server}/login"
        payload = {
            "account": GROWATT_USER,
            "password": get_md5(GROWATT_PASS),
            "validateCode": ""
        }
        try:
            res = session.post(login_url, data=payload, timeout=10)
            data = res.json()
            if data.get("result") == 1:
                login_data = data
                active_server = server
                print(f"✅ Успешный вход через сервер: {server}")
                break
        except Exception:
            continue

    if not login_data:
        print("❌ Ошибка входа Growatt: Не удалось авторизоваться ни на одном сервере. Проверьте правильность логина и пароля.")
        return

    try:
        user_id = login_data.get("userId")
        
        # Запрос информации по даталоггеру
        device_url = f"{active_server}/panel/datalogger/getDataloggerInfo?dataloggerSn={DATALOGGER_SN}"
        dev_res = session.get(device_url, timeout=15)
        dev_data = dev_res.json()
        
        obj = dev_data.get("obj", {})
        
        grid_status = int(obj.get("status", 1)) == 1
        battery_soc = int(float(obj.get("batterySoc", obj.get("capacity", 0))))
        load_power = int(float(obj.get("loadPower", obj.get("pac", 0))))

        # Отправка в Supabase
        supabase.table("power_logs").insert({
            "grid_status": grid_status,
            "battery_soc": battery_soc,
            "load_power": load_power
        }).execute()
        
        print(f"✅ Успешно синхронизировано: Сеть={grid_status}, АКБ={battery_soc}%, Нагрузка={load_power}W")

    except Exception as e:
        print(f"❌ Ошибка обработки данных: {e}")

if __name__ == "__main__":
    fetch_and_push()

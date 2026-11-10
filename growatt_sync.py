import os
import hashlib
import requests
from supabase import create_client

# Настройки Supabase
SUPABASE_URL = "https://nzpfbvrbwmxhhpajgyjj.supabase.co"
SUPABASE_KEY = "sb_publishable_htg_8lgoGKWP7Dx7eVlhDg_eLnr3Y10"

# Авторизация Growatt
GROWATT_USER = "Viachealav"
GROWATT_PASS = "Iloveyara2552"
DATALOGGER_SN = "HAQ1G5H24S"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_md5(password):
    return hashlib.md5(password.encode('utf-8')).hexdigest()

def fetch_and_push():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01"
    })

    try:
        # 1. Авторизация в Growatt (передаем хешированный MD5 пароль)
        login_url = "https://server.growatt.com/login"
        password_md5 = get_md5(GROWATT_PASS)
        
        payload = {
            "account": GROWATT_USER,
            "password": password_md5,
            "validateCode": ""
        }
        
        res = session.post(login_url, data=payload, timeout=15)
        
        # 2. Опрос информации по даталоггеру
        info_url = f"https://server.growatt.com/panel/datalogger/getDataloggerInfo?dataloggerSn={DATALOGGER_SN}"
        res_info = session.get(info_url, timeout=15)
        data = res_info.json()
        
        obj = data.get("obj", {})
        
        grid_status = int(obj.get("status", 1)) == 1
        battery_soc = int(obj.get("batterySoc", obj.get("capacity", 0)))
        load_power = int(obj.get("loadPower", obj.get("pac", 0)))

        # 3. Отправка данных в Supabase
        supabase.table("power_logs").insert({
            "grid_status": grid_status,
            "battery_soc": battery_soc,
            "load_power": load_power
        }).execute()
        
        print(f"✅ Данные записаны: Сеть={grid_status}, АКБ={battery_soc}%, Нагрузка={load_power}W")

    except Exception as e:
        print(f"❌ Ошибка выполнения: {e}")

if __name__ == "__main__":
    fetch_and_push()

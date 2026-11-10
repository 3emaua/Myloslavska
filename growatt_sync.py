import requests
from supabase import create_client

SUPABASE_URL = "https://nzpfbvrbwmxhhpajgyjj.supabase.co"
SUPABASE_KEY = "sb_publishable_htg_8lgoGKWP7Dx7eVlhDg_eLnr3Y10"

GROWATT_USER = "Viachealav"
GROWATT_PASS = "Iloveyara2552"
DATALOGGER_SN = "HAQ1G5H24S"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_and_push():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
        "Referer": "https://server.growatt.com/login"
    })

    try:
        # 1. Авторизация (передаем пароль в чистом виде)
        login_url = "https://server.growatt.com/login"
        payload = {
            "account": GROWATT_USER,
            "password": GROWATT_PASS,
            "validateCode": ""
        }
        
        res = session.post(login_url, data=payload, timeout=15)
        login_data = res.json()
        
        if login_data.get("result") != 1:
            print(f"❌ Ошибка входа Growatt: {login_data}")
            return
            
        user_id = login_data.get("userId")
        
        # 2. Получение данных инвертора по даталоггеру
        device_url = f"https://server.growatt.com/panel/datalogger/getDataloggerInfo?dataloggerSn={DATALOGGER_SN}"
        dev_res = session.get(device_url, timeout=15)
        dev_data = dev_res.json()
        
        obj = dev_data.get("obj", {})
        
        grid_status = int(obj.get("status", 1)) == 1
        battery_soc = int(float(obj.get("batterySoc", obj.get("capacity", 0))))
        load_power = int(float(obj.get("loadPower", obj.get("pac", 0))))

        # 3. Запись в Supabase
        supabase.table("power_logs").insert({
            "grid_status": grid_status,
            "battery_soc": battery_soc,
            "load_power": load_power
        }).execute()
        
        print(f"✅ Успешно синхронизировано: Сеть={grid_status}, АКБ={battery_soc}%, Нагрузка={load_power}W")

    except Exception as e:
        print(f"❌ Ошибка выполнения: {e}")

if __name__ == "__main__":
    fetch_and_push()

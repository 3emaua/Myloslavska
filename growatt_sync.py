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
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "uk-UA,uk;q=0.9,en;q=0.8"
    })

    try:
        # Авторизация через основной сервер
        login_url = "https://server.growatt.com/login"
        payload = {
            "account": GROWATT_USER,
            "password": get_md5(GROWATT_PASS),
            "validateCode": ""
        }
        
        res = session.post(login_url, data=payload, timeout=15)
        login_data = res.json()
        
        if login_data.get("result") != 1:
            print(f"❌ Ошибка входа Growatt: {login_data}")
            return
            

        # Получаем список установок пользователя
        user_id = login_data.get("userId")
        plant_url = f"https://server.growatt.com/panel/plant/getPlantList?userId={user_id}"
        plant_res = session.get(plant_url, timeout=15)
        plant_data = plant_res.json()
        
        plants = plant_data.get("plantList", [])
        if not plants:
            print("⚠️ Установки не найдены в аккаунте.")
            return
            
        plant_id = plants[0].get("plantId")
        
        # Получаем данные инвертора по даталоггеру
        device_url = f"https://server.growatt.com/panel/datalogger/getDataloggerInfo?dataloggerSn={DATALOGGER_SN}"
        dev_res = session.get(device_url, timeout=15)
        dev_data = dev_res.json()
        
        obj = dev_data.get("obj", {})
        
        grid_status = int(obj.get("status", 1)) == 1
        battery_soc = int(float(obj.get("batterySoc", obj.get("capacity", 0))))
        load_power = int(float(obj.get("loadPower", obj.get("pac", 0))))

        # Запись в Supabase
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

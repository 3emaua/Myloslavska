import os
import requests
from supabase import create_client

SUPABASE_URL = "https://nzpfbvrbwmxhhpajgyjj.supabase.co"
SUPABASE_KEY = "sb_publishable_htg_8lgoGKWP7Dx7eVlhDg_eLnr3Y10"

# Используем OpenAPI токен и ваш серийник даталоггера
GROWATT_API = "https://openapi.growatt.com"
GROWATT_TOKEN = os.getenv("GROWATT_TOKEN", "ваш_токен_сюда") # Или подставьте строкой
DATALOGGER_SN = "HAQ1G5H24S"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_and_push():
    headers = {
        "token": GROWATT_TOKEN,
        "Content-Type": "application/json"
    }
    
    # Эндпоинт OpenAPI для получения параметров устройства по серийнику даталоггера
    url = f"{GROWATT_API}/v1/device/datalogger/setting" # Или актуальный метод получения данных девайса
    
    # Попробуем альтернативный эндпоинт получения данных инвертора через open-api
    params = {
        "dataloggerSn": DATALOGGER_SN
    }
    
    try:
        # Запрос к OpenAPI Growatt
        res = requests.get(f"{GROWATT_API}/v1/plant/data", headers=headers, params=params, timeout=15)
        data = res.json()
        
        if data.get("error_code") == 0 or data.get("code") == 0:
            result = data.get("data", {})
            
            grid_status = bool(result.get("gridStatus", 1))
            battery_soc = int(result.get("capacity", result.get("batterySoc", 0)))
            load_power = int(result.get("pac", result.get("loadPower", 0)))
            
            # Отправка в Supabase
            supabase.table("power_logs").insert({
                "grid_status": grid_status,
                "battery_soc": battery_soc,
                "load_power": load_power
            }).execute()
            
            print(f"✅ Успешно синхронизировано через OpenAPI: Сеть={grid_status}, АКБ={battery_soc}%, Нагрузка={load_power}W")
        else:
            print(f"⚠️ Ошибка ответа OpenAPI Growatt: {data}")
            
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")

if __name__ == "__main__":
    fetch_and_push()

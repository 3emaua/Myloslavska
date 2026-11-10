import os
import requests
from supabase import create_client

SUPABASE_URL = "https://nzpfbvrbwmxhhpajgyjj.supabase.co"
SUPABASE_KEY = "sb_publishable_htg_8lgoGKWP7Dx7eVlhDg_eLnr3Y10"

GROWATT_API = "https://openapi.growatt.com"
GROWATT_TOKEN = "kh3w9600ko1723x05n6146290m444921" 
DATALOGGER_SN = "HAQ1G5H24S"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_and_push():
    headers = {
        "token": str(GROWATT_TOKEN).strip(),
        "Content-Type": "application/json"
    }
    
    # Меняем эндпоинт на спецификацию получения деталей инвертора по даталоггеру
    url = f"{GROWATT_API}/v1/device/datalogger/setting" 
    
    # Или запрашиваем через стандартный путь параметров инвертора
    params = {
        "deviceSn": DATALOGGER_SN
    }
    
    try:
        # Сначала проверим метод получения данных инвертора
        res = requests.get(f"{GROWATT_API}/v1/device/invertor/detail", headers=headers, params=params, timeout=15)
        data = res.json()
        
        # Если структура отличается, попробуем универсальный метод
        if data.get("error_code") != 0 and data.get("code") != 0:
            # Запасной вариант запроса параметров даталоггера
            res = requests.get(f"{GROWATT_API}/v1/device/datalogger/info", headers=headers, params={"dataloggerSn": DATALOGGER_SN}, timeout=15)
            data = res.json()

        print(2026, f"Ответ OpenAPI: {data}")

        if data.get("error_code") == 0 or data.get("code") == 0 or "data" in data:
            result = data.get("data", data)
            if isinstance(result, list) and len(result) > 0:
                result = result[0]
            
            grid_status = bool(result.get("gridStatus", result.get("status", 1)))
            battery_soc = int(float(result.get("capacity", result.get("batterySoc", 0))))
            load_power = int(float(result.get("pac", result.get("loadPower", 0))))
            
            supabase.table("power_logs").insert({
                "grid_status": grid_status,
                "battery_soc": battery_soc,
                "load_power": load_power
            }).execute()
            
            print(f"✅ Успешно синхронизировано: Сеть={grid_status}, АКБ={battery_soc}%, Нагрузка={load_power}W")
        else:
            print(f"⚠️ Ответ OpenAPI: {data}")
            
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")

if __name__ == "__main__":
    fetch_and_push()

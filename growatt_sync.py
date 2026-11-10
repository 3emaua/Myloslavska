import os
import requests
from supabase import create_client

SUPABASE_URL = "https://nzpfbvrbwmxhhpajgyjj.supabase.co"
SUPABASE_KEY = "sb_publishable_htg_8lgoGKWP7Dx7eVlhDg_eLnr3Y10"

GROWATT_TOKEN = "kh3w9600ko1723x05n6146290m444921" 
DATALOGGER_SN = "HAQ1G5H24S"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_and_push():
    headers = {
        "token": str(GROWATT_TOKEN).strip(),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    # Пробуем официальный эндпоинт OpenAPI для получения статуса инвертора по даталоггеру
    urls = [
        "https://openapi.growatt.com/v1/device/invertor/setting",
        "https://openapi.growatt.com/v1/plant/data",
        "https://server.growatt.com/panel/datalogger/getDataloggerInfo"
    ]
    
    success = False
    for url in urls:
        try:
            params = {"dataloggerSn": DATALOGGER_SN, "deviceSn": DATALOGGER_SN}
            res = requests.get(url, headers=headers, params=params, timeout=10)
            data = res.json()
            
            print(f"Попытка URL {url}: {data}")
            
            if isinstance(data, dict) and (data.get("error_code") == 0 or data.get("code") == 0 or "obj" in data or "data" in data):
                result = data.get("data", data.get("obj", data))
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
                success = True
                break
        except Exception as e:
            continue
            
    if not success:
        print("❌ Не удалось получить данные ни с одного эндпоинта OpenAPI.")

if __name__ == "__main__":
    fetch_and_push()

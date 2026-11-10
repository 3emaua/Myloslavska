import os
import requests
from supabase import create_client

SUPABASE_URL = "https://nzpfbvrbwmxhhpajgyjj.supabase.co"
SUPABASE_KEY = "sb_publishable_htg_8lgoGKWP7Dx7eVlhDg_eLnr3Y10"

# Ваши данные (токен вставьте строго в кавычки, без лишних символов)
GROWATT_API = "https://openapi.growatt.com"
GROWATT_TOKEN = "kh3w9600ko1723x05n6146290m444921" 
DATALOGGER_SN = "HAQ1G5H24S"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_and_push():
    # Обязательно только ASCII-символы в заголовках
    headers = {
        "token": str(GROWATT_TOKEN).strip(),
        "Content-Type": "application/json"
    }
    
    params = {
        "dataloggerSn": str(DATALOGGER_SN).strip()
    }
    
    try:
        url = f"{GROWATT_API}/v1/plant/data"
        res = requests.get(url, headers=headers, params=params, timeout=15)
        data = res.json()
        
        if data.get("error_code") == 0 or data.get("code") == 0:
            result = data.get("data", {})
            
            grid_status = bool(result.get("gridStatus", 1))
            battery_soc = int(float(result.get("capacity", result.get("batterySoc", 0))))
            load_power = int(float(result.get("pac", result.get("loadPower", 0))))
            
            supabase.table("power_logs").insert({
                "grid_status": grid_status,
                "battery_soc": battery_soc,
                "load_power": load_power
            }).execute()
            
            print(f"✅ Успешно синхронизировано: Сеть={grid_status}, АКБ={battery_soc}%, Нагрузка={load_power}W")
        else:
            print(f"⚠️ Ошибка ответа OpenAPI Growatt: {data}")
            
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")

if __name__ == "__main__":
    fetch_and_push()

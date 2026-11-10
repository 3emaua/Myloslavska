import os
import requests
from supabase import create_client

SUPABASE_URL = "https://nzpfbvrbwmxhhpajgyjj.supabase.co"
SUPABASE_KEY = "sb_publishable_htg_8lgoGKWP7Dx7eVlhDg_eLnr3Y10"

GROWATT_TOKEN = os.getenv("GROWATT_TOKEN")
DATALOGGER_SN = "HAQ1G5H24S"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_and_push():
    if not GROWATT_TOKEN:
        print("❌ Ошибка: В секретах GitHub Actions не найден GROWATT_TOKEN!")
        return

    # Запрос к API Growatt
    url = "https://server.growatt.com/open-api/v1/plant/data"
    headers = {
        "token": GROWATT_TOKEN,
        "Content-Type": "application/json"
    }
    params = {
        "dataloggerSn": DATALOGGER_SN
    }
    
    try:
        res = requests.get(url, headers=headers, params=params, timeout=15)
        
        # Проверяем HTTP статус
        if res.status_code != 200:
            print(f"❌ Ошибка HTTP {res.status_code}: {res.text[:200]}")
            return
            
        data = res.json()
        
        if data.get("error_code") == 0 or data.get("code") == 0:
            result = data.get("data", {})
            # Парсинг параметров
            grid_status = bool(result.get("gridStatus", result.get("status", 1)))
            battery_soc = int(result.get("capacity", result.get("batterySoc", 0)))
            load_power = int(result.get("pac", result.get("loadPower", 0)))
            
            # Отправка в Supabase
            supabase.table("power_logs").insert({
                "grid_status": grid_status,
                "battery_soc": battery_soc,
                "load_power": load_power
            }).execute()
            print(f"✅ Успешно обновлено: Сеть={grid_status}, АКБ={battery_soc}%, Нагрузка={load_power}W")
        else:
            print(f"⚠️ Ошибка Growatt API: {data}")
    except Exception as e:
        print(f"❌ Исключение при выполнении: {e}")

if __name__ == "__main__":
    fetch_and_push()

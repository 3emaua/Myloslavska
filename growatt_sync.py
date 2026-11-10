import os
import requests
from supabase import create_client

# Настройки подключения к Supabase
SUPABASE_URL = "https://nzpfbvrbwmxhhpajgyjj.supabase.co"
SUPABASE_KEY = "sb_publishable_htg_8lgoGKWP7Dx7eVlhDg_eLnr3Y10"

# Получаем токен Growatt (сначала из секретов GitHub Actions, если нет — можно вставить сюда вручную)
GROWATT_TOKEN = os.getenv("GROWATT_TOKEN") or "ВАШ_ТОКЕН_GROWATT"
DATALOGGER_SN = "HAQ1G5H24S"

# Инициализация Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_and_push():
    url = f"https://server.growatt.com/open-api/datalogger/getDataloggerPlantInfo?dataloggerSn={DATALOGGER_SN}"
    headers = {"token": GROWATT_TOKEN}
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        
        if data.get("code") == 0:
            info = data.get("data", {})
            grid_status = int(info.get("status", 1)) == 1
            battery_soc = int(info.get("batterySoc", 0))
            load_power = int(info.get("loadPower", 0))
            
            # Отправляем данные в таблицу power_logs
            supabase.table("power_logs").insert({
                "grid_status": grid_status,
                "battery_soc": battery_soc,
                "load_power": load_power
            }).execute()
            print(f"✅ Данные успешно обновлены: Сеть={grid_status}, АКБ={battery_soc}%, Нагрузка={load_power}W")
        else:
            print(f"⚠️ Ответ Growatt API: {data}")
    except Exception as e:
        print(f"❌ Ошибка отправки запроса: {e}")

if __name__ == "__main__":
    fetch_and_push()

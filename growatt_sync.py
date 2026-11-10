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

    # Пробуем официальный эндпоинт для даталоггера
    url = f"https://server.growatt.com/open-api/datalogger/getDataloggerPlantInfo?dataloggerSn={DATALOGGER_SN}"
    headers = {"token": GROWATT_TOKEN}
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        print(f"📥 HTTP Статус ответа Growatt: {res.status_code}")
        print(f"📄 Текст ответа: {res.text[:300]}") # Выведем первые 300 символов ответа
        
        # Пытаемся распарсить JSON безопасно
        data = res.json()
        
        if data.get("code") == 0:
            info = data.get("data", {})
            grid_status = int(info.get("status", 1)) == 1
            battery_soc = int(info.get("batterySoc", 0))
            load_power = int(info.get("loadPower", 0))
            
            supabase.table("power_logs").insert({
                "grid_status": grid_status,
                "battery_soc": battery_soc,
                "load_power": load_power
            }).execute()
            print(f"✅ Успешно записано в Supabase: Сеть={grid_status}, АКБ={battery_soc}%, Нагрузка={load_power}W")
        else:
            print(f"⚠️ API Growatt вернул ошибку кода: {data}")
            
    except Exception as e:
        print(f"❌ Ошибка парсинга или запроса: {e}")

if __name__ == "__main__":
    fetch_and_push()

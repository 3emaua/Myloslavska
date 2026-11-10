import sys
import datetime as dt

# Патч совместимости UTC для старых версий Python перед импортом growattServer
if not hasattr(dt, "UTC"):
    from datetime import timezone
    dt.UTC = timezone.utc
    sys.modules["datetime"] = dt

from growattServer import GrowattApi
from supabase import create_client

SUPABASE_URL = "https://nzpfbvrbwmxhhpajgyjj.supabase.co"
SUPABASE_KEY = "sb_publishable_htg_8lgoGKWP7Dx7eVlhDg_eLnr3Y10"

GROWATT_USER = "Viachealav"
GROWATT_PASS = "Iloveyara2552"
DATALOGGER_SN = "HAQ1G5H24S"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_and_push():
    try:
        api = GrowattApi()
        login_response = api.login(GROWATT_USER, GROWATT_PASS)
        
        if not login_response or 'userId' not in login_response:
            print(f"❌ Ошибка авторизации Growatt: {login_response}")
            return
            
        user_id = login_response['userId']
        plants_data = api.plant_list(user_id)
        
        if not plants_data:
            print("⚠️ Установки не найдены для данного аккаунта.")
            return
            
        plant_id = plants_data[0]['plantId']
        devices = api.device_list(plant_id)
        
        grid_status = True
        battery_soc = 0
        load_power = 0
        
        if devices:
            device_sn = devices[0].get('deviceSn')
            device_type = devices[0].get('deviceType', 0)
            det = api.device_detail(device_type, device_sn)
            
            battery_soc = int(float(det.get('batterySoc', det.get('capacity', 0))))
            load_power = int(float(det.get('pLocalLoad', det.get('loadPower', 0))))
            grid_status = int(det.get('status', 1)) == 1

        supabase.table("power_logs").insert({
            "grid_status": grid_status,
            "battery_soc": battery_soc,
            "load_power": load_power
        }).execute()
        
        print(f"✅ Успешно синхронизировано: Сеть={grid_status}, АКБ={battery_soc}%, Нагрузка={load_power}W")

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    fetch_and_push()

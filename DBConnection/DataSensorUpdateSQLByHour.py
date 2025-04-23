# -*- coding: utf-8 -*-
from DBConnection.ConnectSQL import DataSensorCheck
from datetime import datetime
import sys, logging, os

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

waiting_time_list = set()
waiting_hour_list = set()

# Setup logging
# === Configure Logging ======
LOG_FILE = "Logs/DATA_AI_ENGINE_service.log"
os.makedirs("Logs", exist_ok=True)  # Ensure log folder exists

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Clear previous handlers
if logger.hasHandlers():
    logger.handlers.clear()

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# File handler
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8", mode='a')
file_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(console_handler)
logger.addHandler(file_handler)
# ===========================

def UpdateDataSensorByHour(input_json_path):

    now = datetime.now()
    minute, hour = now.minute, now.hour
    waiting_time_list.add(minute)
    waiting_hour_list.add(hour)

    sorted_minutes = sorted(waiting_time_list)
    min_diff = abs(sorted_minutes[0] - sorted_minutes[-1]) if len(sorted_minutes) > 1 else 0

    # Conditions
    is_min_trigger = len(waiting_time_list) > 15
    is_hour_trigger = len(waiting_hour_list) == 2

    triggered = False

    if is_min_trigger and min_diff >= 15:
        logger.info(f"SENSOR DATA By Hour Check : {now.strftime('%d/%m/%Y %H:%M:%S')}")
        DataSensorCheck(input_json_path)
        triggered = True
        waiting_time_list.clear()
        logger.info(f"SENSOR DATA By Hour Last update : {now.strftime('%d/%m/%Y %H:%M:%S')}")

    if is_hour_trigger and not triggered:
        logger.info(f"SENSOR DATA By Hour Check : {now.strftime('%d/%m/%Y %H:%M:%S')}")
        DataSensorCheck(input_json_path)
        triggered = True
        waiting_time_list.clear()
        waiting_hour_list.clear()
        logger.info(f"SENSOR DATA By Hour Last update : {now.strftime('%d/%m/%Y %H:%M:%S')}")
    
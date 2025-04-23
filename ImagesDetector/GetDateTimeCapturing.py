# -*- coding: utf-8 -*-
import platform
from DBConnection import ConnectSQL
import logging
import os, sys
from datetime import datetime
from ImagesDetector.GetImageInfo import getDate

# Setup logging
# === Configure Logging ===
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


def capturingDate(imgName):
    try:
        #t = os.path.getctime(imgName)
        t = getDate(imgName)
        #print(t)
        datetime_object = datetime.fromtimestamp(t)
        #print(datetime_object)
        test = datetime.now()
        c= '.'
        c_index = ([pos + 1 for pos, char in enumerate(str(test)) if char == c])
        if (len(c_index) >= 1):
            capturingDate = str(datetime_object)[:c_index[0]-1]
        format_data = "%Y-%m-%d %H:%M:%S"
        datetime_object = datetime.strptime(test, format_data)
        #print(datetime_object)
        logger.info("Thời gian ảnh chụp: " + str(datetime_object))
        return datetime_object
    except Exception as e:
        logger.error(f" ImagesDetector.GetDateTimeCapturing.capturingDate: \n{e}\n")
        #print("Không thể tìm thấy thời gian ảnh chụp")

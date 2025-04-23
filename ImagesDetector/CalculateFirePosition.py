from math import asin, atan2, cos, degrees, radians, sin
import logging
import math, os, sys

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

def calculateDistance(imageWidthPx):
    # lat1 = lat1 * math.pi / 180
    # lon1 = lon1 * math.pi / 180
    # lat2 = lat2 * math.pi / 180
    # lon2 = lon2 * math.pi / 180
    # # chuyển đổi từ độ sang radian
    # R = 6371  # Earth's radius in kilometers
    # dlat = lat2 - lat1
    # dlon = lon2 - lon1
    # a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    # c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    # return R * c
    #dotthu khoangcach=1.2km, duongkinh 5m, AInhandien 450 pixel
    pass

def calDistance(objectH,imageObjectHeigh):
    d = (objectH * 4.8 * 1080 / imageObjectHeigh)/1000
    #print (f"distance: {d}")
    logger.info(f"distance: {d}")

def calculateDiameter(w,h,scale=0.01):

    width = w * 0.01
    height = h * 0.01
    return width , height
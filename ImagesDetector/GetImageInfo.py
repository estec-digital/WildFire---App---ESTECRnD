from PIL import Image as PImage
#from ImagesDetector.GetDateTimeCapturing import capturingDate
from DBConnection import ConnectSQL
import logging, os, sys, re
from datetime import datetime

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

def getDate(imageName):
    try:
        # Extract date and time using regex
        match = re.search(r"_(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})", imageName)
        if match:
            capturingDate = match.group(1)
            capturingTime = match.group(2).replace("-", ":")
            capturing_img_date = f"{capturingDate} {capturingTime}"
            format_data = "%Y-%m-%d %H:%M:%S"
            datetime_object = datetime.strptime(capturing_img_date, format_data)
            return datetime_object, f"{capturingDate} {capturingTime[:-3]}"
        else:
            raise ValueError("Image name doesn't contain valid datetime format")
    except Exception as e:
        logger.error(f"ImagesDetector.GetImageInfo.getDate: \n{e}\n")
        return None, None


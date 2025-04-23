import os, sys, logging
from datetime import datetime
from PIL import Image as PImage

# Setup logging
LOG_FILE = "Logs/DATA_AI_ENGINE_service.log"
os.makedirs("Logs", exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if logger.hasHandlers():
    logger.handlers.clear()

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8", mode='a')
file_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

# ===========================

def saveImgAngle(imgPath):
    """Create angle folders inside imgPath from 0 to 345 with step 15"""
    try:
        for angle in range(0, 360, 15):
            angle_folder = os.path.join(imgPath, str(angle))
            os.makedirs(angle_folder, exist_ok=True)
        logger.info(f"Angle folders created successfully in: {imgPath}")
    except Exception as e:
        logger.error(f"[ERROR] Creating angle folders: {e}")


def getGoc(file, angleFolder, folderName, imgPath):
    """
    Save image to corresponding angle folder if angle matches folderName
    and current time is before 17h
    """
    try:
        parts = file.split('_')
        if len(parts) >= 7 and 'Goc' in parts[6]:
            # Extract angle part
            angle_str = parts[6].replace('Goc', '').replace('Huong', '').replace('-', '')
            angle = round(float(angle_str))
            if angle == folderName:
                now = datetime.now()
                if now.hour <= 17:
                    image = PImage.open(imgPath)
                    save_path = os.path.join(angleFolder, file)
                    image.save(save_path)
                    logger.info(f"[SAVED] {file} => {save_path}")
    except Exception as e:
        logger.error(f"[ERROR] Processing {file}: {e}")

import shutil
from datetime import datetime, timedelta
import os,time, json
import logging, os, sys

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


def delFolder(days_threshold, input_json_path):
    try:
        saveFolder = getFolder(input_json_path)
        now = datetime.now()
        if not os.path.exists(saveFolder):
            os.makedirs(saveFolder)

        list_file = os.listdir(saveFolder)
        #sort by created time
        list_file.sort(key=lambda x: os.stat(os.path.join(saveFolder, x)).st_mtime)
        # for file in parent_files:
        for file in list_file:
            
            folder_path = saveFolder + "\\" + file
            folder_mtime = os.path.getmtime(folder_path)

            folder_date = datetime.fromtimestamp(folder_mtime)
    
            if (int(now.month - folder_date.month) >= 1 or (int(now.day - folder_date.day) > days_threshold) or (int(now.year - folder_date.year) >= 1)):
                    items = os.listdir(folder_path)
                    for item in items:
                            item_path = folder_path  + "\\" + item
                            item_mtime = os.path.getmtime(item_path)
                            item_date = datetime.fromtimestamp(item_mtime)
                            if (10 < int(item_date.hour) <= 11 and int(item_date.minute) > 30):
                                pass
                            else:
                                os.remove(item_path)
                                #print("Delete file: " + str(item_path))
                                logger.info("Delete file: " + str(item_path))
    except Exception as e:
        #print(e)
        logger.error(f" ImagesDetector.RemoveFolder.delFolder: {e}")

def getFolder(input_json_path):
    try:
        with open(input_json_path, encoding="utf-8") as f:
            config = json.load(f)
        save_folder = config.get("Soc_son_path_web")
        if not save_folder:
            raise ValueError("Missing 'Soc_son_path_web' in config")
        return save_folder
    except Exception as e:
        logger.error(f"[ERROR] getFolder(): {e}")
        input_path = input("Nhập đường dẫn thư mục ảnh cần xoá: ")
        return input_path

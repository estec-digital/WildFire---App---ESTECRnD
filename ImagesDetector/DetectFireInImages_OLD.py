# -*- coding: utf-8 -*-
from PIL import Image as PImage
import os
import logging
from ImagesDetector.InsertData import insertSQL_tbDamChay, send_email_Damchay
from ImagesDetector.SaveImage import save
from datetime import datetime, timedelta
from ImagesDetector import GetImageInfo
from UserInput import InputSendReceive
from UserInput.InputMSGToken import iSMGToken
import time
from UserInput.InputEmailSendReceive import emailSenderReciever
import sys

last_email_time = None

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

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

imageList = []
infoList = []
saveImageList = []
count = 0
limit_count = 0
count_log = 0

def extract_time_from_filename(filename):
    try:
        # filename example: image_SocSon_2025-04-06_20-29-20_Goc_195.0_Huong_0.0_Zoom_1.0.jpg
        parts = filename.split("_")
        datetime_str = parts[2] + " " + parts[3]  # "2025-04-06 20-29-20"
        dt = datetime.strptime(datetime_str, "%Y-%m-%d %H-%M-%S")
        return dt
    except Exception as e:
        logger.error(f"[FILENAME ERROR] Cannot extract timestamp from {filename}: {e}")
        return None
    
def is_file_ready(filepath):
    """Check if file can be safely opened."""
    try:
        with open(filepath, 'rb') as f:
            f.read(1)
        return True
    except:
        return False 
    
def loadImageFolder(images_path, destination, server, fire_trainedModel, input_json_path)-> None:
    global count_log
    global last_email_time
    
    try:
        # Step 1: Get all files in the directory
        if count_log % 50 == 0:
            logger.info(f"AI ENGINE running ...")
            count_log = 0
        
        count_log += 1
        all_files = [
            f for f in os.listdir(images_path)
            if f.lower().endswith((".jpg", ".jpeg", ".png")) and "image_SocSon" in f
        ]

        files_with_time = []
        for file in all_files:
            ts = extract_time_from_filename(file)
            if ts:
                files_with_time.append((file, ts))

        # Step 2: Sort by newest
        files_with_time.sort(key=lambda x: x[1], reverse=True)
        latest_files = files_with_time[:30]

        # Ensure destination folder exists
        folder_date = datetime.now().strftime("%Y-%m-%d")
        saveResultFolder = os.path.join(destination, folder_date)
        os.makedirs(saveResultFolder, exist_ok=True)
        
        #logger.info("AI ENGINE running ...")

        # Step 3: Loop through the latest 30 images
        for file, ts in latest_files:
            try:
                now = datetime.now()
                image_path = os.path.join(images_path, file)
                KHTram = "SocSon"

                # img_capturing_Date = str(GetImageInfo.getDate(file))
                # if img_capturing_Date == "None":
                #     logger.warning(f"[SKIP] Cannot determine capture date, removing: {file}")
                #     os.remove(image_path)
                #     pass

                #  Ensure file is fully written
                if not is_file_ready(image_path):
                    logger.warning(f"[SKIP] File not ready for read: {file}")
                    return

                #  Try safely extracting date
                try:
                    img_capturing_Date = str(GetImageInfo.getDate(file))
                except Exception as e:
                    logger.warning(f"[SKIP] Failed to parse image date: {e}")
                    return

                if img_capturing_Date == "None":
                    logger.warning(f"[SKIP] Date not found, removing: {file}")
                    os.remove(image_path)
                    return

                #logger.info(f"[PROCESSING] Inference on: {file}")
                getResults(now, image_path, saveResultFolder, file, KHTram, server, fire_trainedModel, input_json_path)
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"[ERROR] load() processing file {file}: {e}")
                time.sleep(0.1)
                return

    except Exception as e:
        logger.error(f"[LOAD ERROR] ImagesDetector.DetectFireInImages.load: {e}")
        time.sleep(0.1)
        return 

def getResults(now, image_path, saveFolder, imageName, KHTram, server, fire_trainedModel, input_json_path)-> None:
    global last_email_time

    sender_email, sender_password = emailSenderReciever(input_json_path)

    if not os.path.exists(image_path):
        logger.warning(f"[SKIPPED] Image not found: {image_path}")
        return

    # Confirm the file can be read (avoid incomplete saves)
    try:
        with open(image_path, 'rb') as f:
            f.read()
    except Exception:
        logger.warning(f"[SKIPPED] Image locked or unreadable: {image_path}")
        return

    results = fire_trainedModel(image_path)
    df = results.pandas().xyxy[0]

    if not df.empty:
        confidence = df.iloc[0, 4] * 100
        if confidence >= 25:
            global count
            df.iloc[0, 4] = 0.8
            xmin, ymin, xmax, ymax = map(int, df.iloc[0, :4])
            X = (xmax + xmin) / 2
            Y = (ymax + ymin) / 2
            W = xmax - xmin
            H = ymax - ymin

            if W > 60 and H > 60 and H < 950 and Y < 800:
                try:
                    #logger.info(f"[PROCESSING] detected on: {image_path}")
                    save_path = save(results, saveFolder, imageName)
                    if save_path:
                        insertSQL_tbDamChay(df, image_path, saveFolder, imageName, confidence)
                        # send_email_Damchay(server, now.minute, count, df, image_path, saveFolder, imageName, confidence,
                        #     sender_email, sender_password, input_json_path)
                        # count += 1
                        # ===  Email Throttling Check ===
                        now_time = datetime.now()
                        if (last_email_time is None) or (now_time - last_email_time > timedelta(minutes=3)):
                            send_email_Damchay(
                                server, now.minute, count, df, image_path,
                                saveFolder, imageName, confidence,
                                sender_email, sender_password, input_json_path
                            )
                            last_email_time = now_time  # update last email time
                            count += 1
                            time.sleep(0.1)  # Optional: add a small delay to avoid spamming
                        else:
                            logger.info("[EMAIL SKIPPED] Last email was sent less than 3 minutes ago.")
                except Exception as notify_error:
                    logger.error(f"[NOTIFY ERROR] DB/email failed: {notify_error}")
                    return

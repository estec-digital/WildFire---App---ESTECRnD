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
import sys, cv2, json, threading

# Shared flag and lock
detected_results = []  # Shared across threads
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

# === CLEAN UP STEP ===
def clear_folder(folder_path, extensions={'.jpg', '.jpeg', '.png', '.bmp'}):
    if not os.path.exists(folder_path):
        return
    for file in os.listdir(folder_path):
        if os.path.splitext(file)[1].lower() in extensions:
            try:
                os.remove(os.path.join(folder_path, file))
            except Exception as e:
                logger.warning(f"[CLEANUP ERROR] Could not remove {file}: {e}")

def augment_image(image_path, output_folder):
    # Extract image name and extension
    img_name_ext = os.path.basename(image_path)
    img_name, img_ext = os.path.splitext(img_name_ext)
    img_ext = img_ext.lstrip('.')

    # Read original image
    img = cv2.imread(image_path)
    if img is None:
        print(f" Could not read image: {image_path}")
        return

    os.makedirs(output_folder, exist_ok=True)

    # CLAHE enhancement
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    enhanced_img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

    # Save CLAHE images
    cv2.imwrite(os.path.join(output_folder, f"{img_name}_1.{img_ext}"), enhanced_img)
    cv2.imwrite(os.path.join(output_folder, f"{img_name}_2.{img_ext}"), enhanced_img)

    # Brightness and contrast variations
    variations = [
        (1.5, 30),       # (3)
        (1.5, 30),       # (4)
        (2.5, 30),       # (5)
        (1.0, 40),       # (6)
        (1.0, 30),       # (7)
        (1.0, 45),       # (8)
        (1.5, 50)        # (9)
    ]

    for i, (alpha, beta) in enumerate(variations, start=3):
        modified = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)
        cv2.imwrite(os.path.join(output_folder, f"{img_name}_{i}.{img_ext}"), modified)

    #print(f" Augmented images saved to: {output_folder}")

# Define thread worker for augment chunk image folder
def augment_chunk(chunk,images_path, output_folder):
    for file, ts in chunk:
        full_image_path = os.path.join(images_path, file)
        augment_image(full_image_path, output_folder)

# Inferece images
def inference_images(folder_path, saveResultFolder, server, fire_trainedModel, input_json_path):
    global detected_results
    # Supported image extensions
    valid_exts = {'.jpg', '.jpeg', '.png', '.bmp'}
    try:
        image_files = [
            f for f in os.listdir(folder_path)
            if os.path.splitext(f)[1].lower() in valid_exts
        ]

        for file in image_files:
            image_path = os.path.join(folder_path, file)

            if not os.path.exists(image_path):
                # logger.warning(f"[SKIPPED] Image not found: {image_path}")
                continue

            now = datetime.now()
            KHTram = "SocSon"
            try:
                # `getResults` should return True/False or some value if fire is detected
                result = getResults(now, image_path, saveResultFolder, file, KHTram, server, fire_trainedModel, input_json_path)

                if not result:
                    # Delete image if no detection
                    os.remove(image_path)
                    # logger.info(f"[REMOVED] No detection, removed: {file}")
                else:
                    detected_results.append(result)
                    # logger.info(f"[DETECTED] Kept result: {file}")
            except Exception as e:
                # logger.error(f"[ERROR] Inference on {file}: {e}")
                continue
            time.sleep(0.1)

    except Exception as e:
        logger.error(f"[THREAD ERROR] {folder_path}: {e}")

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
    
    #logger.info(f"[PROCESSING] on: {image_path}")

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

            if W > 140 and H > 160 and H < 950 and Y < 800:# W > 145 and H > 109 and H < 950 and Y < 800: #if W > 60 and H > 60 and H < 950 and Y < 800:
                try:
                    #logger.info(f"[PROCESSING] detected on: {image_path}")
                    save_path = save(results, saveFolder, imageName)
                    count += 1
                    return {
                        "df": df,
                        "image_path": image_path,
                        "saveFolder": saveFolder,
                        "imageName": imageName,
                        "confidence": confidence,
                        "server": server,
                        "now": now.minute,
                        "count": count,
                        "sender_email": sender_email,
                        "sender_password": sender_password,
                        "input_json_path": input_json_path
                    }

                except Exception as notify_error:
                    logger.error(f"[NOTIFY ERROR] DB/email failed: {notify_error}")
                    return None


def loadImageFolder(images_path, destination, server, fire_trainedModel, input_json_path)-> None:
    global count_log
    global last_email_time
    global detected_results  # Shared across threads
    detected_results = []  

    # Augmented image data
    with open(input_json_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    aug_1 = config.get("Augment_image_1")
    aug_2 = config.get("Augment_image_2")
    aug_3 = config.get("Augment_image_3")
    
    # Clear old images
    clear_folder(aug_1)         # Clear Augment folder 1
    clear_folder(aug_2)         # Clear Augment folder 2
    clear_folder(aug_3)         # Clear Augment folder 3

    # Ensure destination folder exists
    folder_date = datetime.now().strftime("%Y-%m-%d")
    saveResultFolder = os.path.join(destination, folder_date)
    os.makedirs(saveResultFolder, exist_ok=True)

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
        latest_files = files_with_time[:9]

        # Assume latest_files contains 30 items
        chunk_size = 3
        chunks = [latest_files[i:i + chunk_size] for i in range(0, len(latest_files), chunk_size)]

        # Create threads for each chunk
        threads = [
            threading.Thread(target=augment_chunk, args=(chunks[0],images_path, aug_1)),
            threading.Thread(target=augment_chunk, args=(chunks[1],images_path, aug_2)),
            threading.Thread(target=augment_chunk, args=(chunks[2],images_path, aug_3)),
        ]

        # Start all threads
        for t in threads:
            t.start()
        # Optionally, wait for all threads to complete
        for t in threads:
            t.join()

        # print(f"Completed generated Aug at: {aug_1, aug_2, aug_3}")

        # Threading for inference image and save result in dictionary
        # Create and run threads for inference
        threads = [
            threading.Thread(target=inference_images, args=(aug_1, saveResultFolder, server, fire_trainedModel, input_json_path)),
            threading.Thread(target=inference_images, args=(aug_2, saveResultFolder, server, fire_trainedModel, input_json_path)),
            threading.Thread(target=inference_images, args=(aug_3, saveResultFolder, server, fire_trainedModel, input_json_path)),
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # logger.info(" Inference threads for all augmented folders completed.")

        # Send notification and update DB for result
        if detected_results:
            #logger.info(f"[ALERT] Total fires detected: {len(detected_results)}")
            # Send DB + Email after all are done
            try:
                for idx, result in enumerate(detected_results):
                    # insertSQL_tbDamChay(result["df"], result["image_path"], result["saveFolder"], 
                    #                     result["imageName"], result["confidence"])
                    
                    # Email throttling logic
                    now_time = datetime.now()
                    if (last_email_time is None) or (now_time - last_email_time > timedelta(minutes=3)):
                        insertSQL_tbDamChay(result["df"], result["image_path"], result["saveFolder"], 
                                        result["imageName"], result["confidence"])
                        send_email_Damchay(result["server"], result["now"], result["count"], result["df"],
                                           result["image_path"], result["saveFolder"], result["imageName"], 
                                           result["confidence"], result["sender_email"], result["sender_password"],
                                           result["input_json_path"])
                        last_email_time = now_time
                        time.sleep(1)
                    # else:
                    #     logger.info("[EMAIL SKIPPED] Last email was sent less than 3 minutes ago.")

            except Exception as e:
                logger.error(f"[FINAL ERROR] DB/Email batch failed: {e}")

    except Exception as e:
        logger.error(f"[LOAD ERROR] ImagesDetector.DetectFireInImages.load: {e}")
        time.sleep(0.1)
        return 

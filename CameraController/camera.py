import threading
import time
import requests
from requests.auth import HTTPDigestAuth
import os
import cv2
import numpy as np
import pyodbc
import traceback
from datetime import datetime
from flask import Flask
from flask_cors import CORS
import xml.etree.ElementTree as ET
import logging
import multiprocessing
import sys, ctypes  

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("camera_and_sql_service.log", encoding="utf-8", mode='a')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/toggle_capture_control": {"origins": ["*"]}})

log_camera_save_count = 0
log_camera_rotate_count = 0

# Camera and folder config
camera_ip = 'estecsocson.ddns.net:81'
username = 'admin'
password = 'Pass@work1'
output_folder = 'D:\\EWFDS\\wwwroot\\img\\SocSon'
ai_folder = os.path.join(output_folder, "ImgForAI")
os.makedirs(ai_folder, exist_ok=True)

# Auth and URLs
auth = HTTPDigestAuth(username, password)
status_url = f"http://{camera_ip}/ISAPI/PTZCtrl/channels/1/status"
ptz_url = f"http://{camera_ip}/ISAPI/PTZCtrl/channels/1/Absolute"

def disable_quick_edit():
    if sys.platform == "win32":
        import msvcrt
        kernel32 = ctypes.windll.kernel32
        hStdin = kernel32.GetStdHandle(-10)
        mode = ctypes.c_uint()
        kernel32.GetConsoleMode(hStdin, ctypes.byref(mode))
        new_mode = mode.value & ~0x0040  # Disable ENABLE_QUICK_EDIT_MODE
        kernel32.SetConsoleMode(hStdin, new_mode)

# Insert image metadata into SQL Server
def insert_data_SQL(parameters ):
    connection = pyodbc.connect(
            "Driver={ODBC Driver 17 for SQL Server};"
            "Server=192.168.54.39\\WFDS;Database=WFDS;"
            "Uid=administrator;Pwd=Pass@work1"
        )

    try:
        cursor = connection.cursor()
        cursor.executemany(
            "INSERT INTO tbAnhz (Image_name, Image_angle, Image_time, MaTram) VALUES (?, ?, ?, ?)",
            parameters
        )
        connection.commit()
        #connection.close()
        return True
    except Exception as e:
        #connection.close()
        logger.error(f"[DB ERROR] {e}")
        time.sleep(1)
        return None

# Capture image from camera
def capture(pan, tilt, zoom):
    global log_camera_save_count
    url = f"http://{camera_ip}/ISAPI/Streaming/channels/1/picture"
    log_camera_save_count += 1
    try:
        response = requests.get(url, headers={"Content-Type": "application/xml"}, auth=auth, timeout=10)
        if response.status_code == 200:
            image_array = np.frombuffer(response.content, np.uint8)
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            if frame is not None:
                now = datetime.now()
                date_str = now.strftime("%Y-%m-%d")
                time_str = now.strftime("%H-%M-%S")
                #image_filename = f"image_SocSon_{date_str}_{time_str}_Goc_{pan/10}_Huong_{tilt/10}_Zoom_{zoom/10}.jpg"
                # Convert pan to degrees and round to nearest 15 degrees
                angle_deg = round((pan / 10) / 15) * 15
                if angle_deg >= 360:
                    angle_deg = 0  # Wrap around
                image_filename = f"image_SocSon_{date_str}_{time_str}_Goc_{angle_deg:.1f}_Huong_{tilt/10}_Zoom_{zoom/10}.jpg"

                folder_path = os.path.join(output_folder, date_str)
                os.makedirs(folder_path, exist_ok=True)
                image_path = os.path.join(folder_path, image_filename)
                cv2.imwrite(image_path, frame)

                insert_sql = insert_data_SQL([[image_filename, pan / 10, now, "SocSon"]])
                if not insert_sql:
                    logger.error("Failed to insert SQL")
                #save_to_ai_folder(image_path, image_filename)

                if log_camera_save_count %50 == 0:
                    logger.info(f"[CAPTURE] Saved: {image_filename}")
                    log_camera_save_count = 0
                return image_filename
            else:
                logger.warning("[CAPTURE] Failed to decode image.")
        else:
            logger.warning(f"[CAPTURE] HTTP {response.status_code}")
    except Exception as e:
        logger.error(f"[CAPTURE ERROR] {e}")
    return None

# Get current PTZ status
def get_status_requests():
    try:
        response = requests.get(status_url, headers={"Content-Type": "application/xml"}, auth=auth, timeout=10)
        response.raise_for_status()
        ns = {"ns": "http://www.hikvision.com/ver20/XMLSchema"}
        root = ET.fromstring(response.content)
        high = root.find(".//ns:AbsoluteHigh", ns)
        if high is not None:
            pan = int(high.find(".//ns:azimuth", ns).text)
            tilt = int(high.find(".//ns:elevation", ns).text)
            zoom = int(high.find(".//ns:absoluteZoom", ns).text)
            return pan, tilt, zoom
    except Exception as e:
        logger.error(f"[STATUS ERROR] {e}")
    return None, None, None

# Send PTZ move request
def send_ptz(angle):
    xml_payload = f"""<?xml version="1.0" encoding="UTF-8"?>
    <PTZData>
        <AbsoluteHigh>
            <elevation>0</elevation>
            <azimuth>{angle}</azimuth>
            <absoluteZoom>10</absoluteZoom>
        </AbsoluteHigh>
    </PTZData>"""
    global log_camera_rotate_count
    log_camera_rotate_count += 1
    try:
        response = requests.put(ptz_url, data=xml_payload, headers={"Content-Type": "application/xml"}, auth=auth, timeout=10)
        response.raise_for_status()
        if log_camera_rotate_count %50 == 0:
            logger.info(f"[PTZ] Moved to {angle / 10:.1f}°")
            log_camera_rotate_count = 0
    except Exception as e:
        logger.error(f"[PTZ ERROR] {e}")

# Main loop
def capture_loop():
    angle = 0
    interval = 6  # seconds
    next_capture_time = time.time()

    while True:
        pan, tilt, zoom = get_status_requests()
        if pan is not None:
            capture(pan, tilt, zoom)
            send_ptz(angle)
            angle = (angle + 150) % 3600
        else:
            logger.warning("[LOOP] PTZ status not available.")

        # Đồng bộ thời gian thực
        next_capture_time += interval
        now = time.time()
        sleep_time = next_capture_time - now

        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            logger.warning(f"[WARNING] Capture loop delayed by {-sleep_time:.2f} seconds")
            # Nếu chệch hơn 2 chu kỳ → reset lại mốc thời gian
            if -sleep_time > 2 * interval:
                next_capture_time = now


def start_flask():
    logger.info("[FLASK] Server started.")
    app.run(host='0.0.0.0', port=5000, use_reloader=False)

if __name__ == '__main__':
    disable_quick_edit()  # Disable quick edit mode for Windows console
    multiprocessing.freeze_support()  # for Windows support

    try:
        logger.info("[MAIN] Starting Camera monitoring service...")

        capture_process = multiprocessing.Process(target=capture_loop)
        capture_process.start()

        flask_process = multiprocessing.Process(target=start_flask)
        flask_process.start()

        # Watchdog loop
        while True:
            if not capture_process.is_alive():
                logger.warning("[WATCHDOG] capture_process died. Restarting...")
                capture_process = multiprocessing.Process(target=capture_loop)
                capture_process.start()
                capture_process.join()

            if not flask_process.is_alive():
                logger.warning("[WATCHDOG] flask_process died. Restarting...")
                flask_process = multiprocessing.Process(target=start_flask)
                flask_process.start()

            time.sleep(10)

    except KeyboardInterrupt:
        logger.warning("[MAIN] Interrupted by user. Exiting...")

    except Exception as e:
        logger.error(f"[MAIN ERROR] {e}")
        traceback.print_exc()
        time.sleep(10)

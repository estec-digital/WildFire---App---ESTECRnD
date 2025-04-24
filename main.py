# -*- coding: utf-8 -*-
import sys, logging, os, time, json
import smtplib, ctypes, signal
import threading, subprocess, traceback
from ImagesDetector import DetectFireInImages
from UserInput.InputPathDes import pathDes
from datetime import datetime
from UserInput.InputEmailSendReceive import emailSenderReciever
from ModelLoader import LoadTrainedModel
from DBConnection import ConnectSQL 
from DBConnection.DataSensorUpdateSQLByHour import UpdateDataSensorByHour
from UserInput.InputDB import db 
from ImagesDetector.RemoveFolder import delFolder
import concurrent.futures
from DBConnection.ConnectSQL import DataSensorCheck    

# === Configure UTF-8 Console Output ===
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# === Configure Logging ===
LOG_FILE = "Logs/DATA_AI_ENGINE_service.log"
os.makedirs("Logs", exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if logger.hasHandlers():
    logger.handlers.clear()

console_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8", mode='a')

formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)
# ===========================

def disable_quick_edit():
    if sys.platform == "win32":
        import msvcrt
        kernel32 = ctypes.windll.kernel32
        hStdin = kernel32.GetStdHandle(-10)
        mode = ctypes.c_uint()
        kernel32.GetConsoleMode(hStdin, ctypes.byref(mode))
        new_mode = mode.value & ~0x0040  # Disable ENABLE_QUICK_EDIT_MODE
        kernel32.SetConsoleMode(hStdin, new_mode)

def detector(input_json_path):
    img_path, destination = pathDes(input_json_path)
    sender_email, sender_password = emailSenderReciever(input_json_path)

    fire_trainedModel = LoadTrainedModel.loadModel(input_json_path)

    with open(input_json_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    tram_img_folder = config.get("Soc_son_path_web")

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.login(sender_email, sender_password)

    logger.info(f"AI ENGINE running ...")

    while True:
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                #logger.info(f"DATA SENSOR running ...")
                future = executor.submit(UpdateDataSensorByHour, input_json_path)

            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            folder_path = os.path.join(tram_img_folder, date_str)

            # AI Engine Service
            DetectFireInImages.loadImageFolder(folder_path, destination, server, fire_trainedModel, input_json_path)
            
            # Remove old images longer than 30 days
            delFolder(30, input_json_path)

            # data_threading.join()
            time.sleep(2)

        except Exception as e:
            logger.error(f"[DETECTOR LOOP ERROR] {e}")
            time.sleep(5)

def parse_config_argument():
    default_path = "D:\\ChayRungProject\\FireDetector\\input.json"
    for arg in sys.argv[1:]:
        if arg.startswith("config="):
            return arg.split("=", 1)[1]
    return default_path

def start_sensor_by_hour_script():
    sensor_script_path = "D:\\ChayRungProject\\FireDetector\\main_Sensor.py"
    python_executable = "python"  # Or full path to Python if needed

    sensor_hour_process = subprocess.Popen([python_executable, sensor_script_path], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

    return sensor_hour_process

def start_camera_script():
    camera_script_path = "D:\\ChayRungProject\\FireDetector\\CameraController\\camera.py"
    python_executable = "python"  # Or full path to Python if needed

    camera_process = subprocess.Popen([python_executable, camera_script_path], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

    return camera_process

def start_camera_notification():
    camera_script_path = "D:\\ChayRungProject\\FireDetector\\CameraController\\cam_notification.py"
    python_executable = "python"  # Or full path to Python if needed

    camera_notification_process = subprocess.Popen([python_executable, camera_script_path], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

    return camera_notification_process

def start_sql_sensor_notification():
    camera_script_path = "D:\\ChayRungProject\\FireDetector\\DBConnection\\SQL_notification.py"
    python_executable = "python"  # Or full path to Python if needed

    camera_notification_process = subprocess.Popen([python_executable, camera_script_path], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

    return camera_notification_process


def main():
    disable_quick_edit()
    
    input_json_path = parse_config_argument()
    logger.info(f"Starting AI Engine Service with config: {input_json_path}")
    camera_process = start_camera_script()

    camera_notification = start_camera_notification()

    sql_sensor_notification = start_sql_sensor_notification()

    # Load credentials from JSON
    SERVER, USERNAME, PASSWORD, DATABASE = db(json_path=input_json_path)
    # Configure the database module with credentials
    ConnectSQL.configure_db(SERVER, USERNAME, PASSWORD, DATABASE)

    # load data sensor
    sensor_by_hour = start_sensor_by_hour_script()
    #DataSensorCheck(input_json_path)
    logger.info("SENSOR DATA SQL Working on data sensor done...")

    try:
        while True:
            detector(input_json_path)

    except KeyboardInterrupt:
        logger.warning("[MAIN] Ctrl+C detected. Stopping services...")

        # Kill the camera subprocess
        if camera_process.poll() is None:
            camera_process.send_signal(signal.CTRL_BREAK_EVENT)  # For Windows
            camera_process.wait()

            camera_notification.send_signal(signal.CTRL_BREAK_EVENT)
            camera_notification.wait()
            logger.info("[MAIN] Camera subprocess terminated.")
            
        if sql_sensor_notification.poll() is None:
            sql_sensor_notification.send_signal(signal.CTRL_BREAK_EVENT)
            sql_sensor_notification.wait()
            logger.info("[MAIN] SQL Data notification process terminated")

        if sensor_by_hour.poll() is None:
            sensor_by_hour.send_signal(signal.CTRL_BREAK_EVENT)
            sensor_by_hour.wait()
            logger.info("[MAIN] Sensor by HOUR process terminated")

    except Exception as e:
        logger.error(f"[MAIN LOOP ERROR] {e}")
        # Kill the camera subprocess
        if camera_process.poll() is None:
            camera_process.send_signal(signal.CTRL_BREAK_EVENT)  # For Windows
            camera_process.wait()

            camera_notification.send_signal(signal.CTRL_BREAK_EVENT)
            camera_notification.wait()
            logger.info("[MAIN] Camera subprocess terminated.")
            
        if sql_sensor_notification.poll() is None:
            sql_sensor_notification.send_signal(signal.CTRL_BREAK_EVENT)
            sql_sensor_notification.wait()
            logger.info("[MAIN] SQL Data notification process terminated")

        if sensor_by_hour.poll() is None:
            sensor_by_hour.send_signal(signal.CTRL_BREAK_EVENT)
            sensor_by_hour.wait()
            logger.info("[MAIN] Sensor by HOUR process terminated")
   

if __name__ == "__main__":
    main()
   

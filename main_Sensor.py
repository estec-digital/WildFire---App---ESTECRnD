# -*- coding: utf-8 -*-
import sys, logging, os, time, json, ctypes, traceback
from UserInput.InputPathDes import pathDes
from DBConnection import ConnectSQL 
from DBConnection.DataSensorUpdateSQLByHour import UpdateDataSensorByHour
from UserInput.InputDB import db 
from ImagesDetector.RemoveFolder import delFolder
from DBConnection.ConnectSQL import DataSensorCheck    
from Logs.LoggerConfig import LoggerSetup

# === Configure UTF-8 Console Output ===
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

def disable_quick_edit():
    if sys.platform == "win32":
        import msvcrt
        kernel32 = ctypes.windll.kernel32
        hStdin = kernel32.GetStdHandle(-10)
        mode = ctypes.c_uint()
        kernel32.GetConsoleMode(hStdin, ctypes.byref(mode))
        new_mode = mode.value & ~0x0040  # Disable ENABLE_QUICK_EDIT_MODE
        kernel32.SetConsoleMode(hStdin, new_mode)

def parse_config_argument():
    default_path = "D:\\ChayRungProject\\FireDetector\\input.json"
    for arg in sys.argv[1:]:
        if arg.startswith("config="):
            return arg.split("=", 1)[1]
    return default_path

def main():
    disable_quick_edit()
    input_json_path = parse_config_argument()
    #logger.info(f"Starting AI Engine Service with config: {input_json_path}")

    # Load credentials from JSON
    SERVER, USERNAME, PASSWORD, DATABASE = db(json_path=input_json_path)
    # Configure the database module with credentials
    ConnectSQL.configure_db(SERVER, USERNAME, PASSWORD, DATABASE)

    # load data sensor
    DataSensorCheck(input_json_path)
    #logger.info("SENSOR DATA SQL Working on data sensor done...")
    # Load config
    with open(input_json_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    log_file = config.get("log_data_sensor")

    # Initialize logger
    logger = LoggerSetup(log_file).get_logger()

    logger.info(" Logger started from configuration")

    while True:
        try:
            UpdateDataSensorByHour(input_json_path)
            # delFolder(30, input_json_path)
            #detector(input_json_path)
        except Exception as e:
            logger.error(f"[MAIN LOOP ERROR] {e}")
            time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("[MAIN] Interrupted by user. Exiting...")

    except Exception as e:
        logger.error(f"[MAIN ERROR] {e}")
        traceback.print_exc()
        time.sleep(10)

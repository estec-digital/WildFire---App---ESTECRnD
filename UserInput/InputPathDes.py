# from Model.FireModel import FireModel
import logging, os, sys, json

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

# fm = FireModel()

def pathDes(json_path):
    try:
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"MIssing json input file: {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        if config.get("project") != "DuAnChayRung":
            raise ValueError("Wrong key value of project.")

        img_path = config.get("AI_img_folder")
        destination = config.get("AI_save_result_folder")

        if not img_path or not destination:
            raise ValueError("Missing information in input.json")

        logger.info(f"[CONFIG] Image folder: {img_path}")
        logger.info(f"[CONFIG] Save results to: {destination}")

        return img_path, destination

    except Exception as e:
        logger.error(f"[pathDes ERROR] {e}")
        path = input("Path to image for AI Engine work: ")
        dst = input("Path to result of AI Engine save: ")
        return path, dst
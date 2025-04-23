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


def emailSenderReciever(json_path):
    if not os.path.exists(json_path):
        logger.error(f"[CONFIG] File not found: {json_path}")
        raise FileNotFoundError(f"Could not find {json_path}")

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        if config.get("project") != "DuAnChayRung":
            logger.warning("[CONFIG] Wrong key 'project'.")
            raise ValueError("Invalid project key in JSON.")

        sender_email = config.get("Email_sender", "")
        sender_password = config.get("Email_password", "")

        if not sender_email or not sender_password:
            raise ValueError("Email sender or password is missing in config file.")

        return sender_email, sender_password

    except json.JSONDecodeError as e:
        logger.error(f"[CONFIG] JSON decode error: {e}")
        raise
    except Exception as e:
        logger.error(f"[EMAIL CONFIG ERROR] {e}")
        raise

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


def SendReceive(json_path):
    try:
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"Không tìm thấy file cấu hình: {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        if config.get("project") != "DuAnChayRung":
            raise ValueError("Thiếu hoặc sai giá trị khóa 'project'.")

        sender = config.get("sms_sender")
        receivers = config.get("sms_receivers")

        if not sender or not receivers:
            raise ValueError("Thiếu thông tin người gửi hoặc người nhận SMS.")

        # Trả về người gửi và danh sách người nhận (nếu chỉ dùng 1 người nhận thì lấy phần tử đầu tiên)
        return sender, receivers[0] if isinstance(receivers, list) and receivers else None

    except Exception as e:
        logger.error(f"[SendReceive ERROR] {e}")
        sender = input("Số điện thoại người gửi (mẫu +16572174079): ")
        receiver = input("Số điện thoại người nhận (mẫu +84362813231): ")
        return sender, receiver
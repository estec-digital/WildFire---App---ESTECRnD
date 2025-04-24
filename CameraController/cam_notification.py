import requests
import smtplib, logging, sys
import time, traceback
from email.mime.text import MIMEText
from datetime import datetime  
import json
import os, ctypes

def disable_quick_edit():
    if sys.platform == "win32":
        import msvcrt
        kernel32 = ctypes.windll.kernel32
        hStdin = kernel32.GetStdHandle(-10)
        mode = ctypes.c_uint()
        kernel32.GetConsoleMode(hStdin, ctypes.byref(mode))
        new_mode = mode.value & ~0x0040  # Disable ENABLE_QUICK_EDIT_MODE
        kernel32.SetConsoleMode(hStdin, new_mode)

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

# Cấu hình email
input_json_path = 'D:/ChayRungProject/FireDetector/input.json'
with open(input_json_path, 'r', encoding='utf-8') as file:
    data = json.load(file)
sender_email, sender_password = emailSenderReciever(input_json_path)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = sender_email
EMAIL_PASSWORD = sender_password

# Danh sách email người nhận
EMAIL_RECEIVERS = data["Email_receivers"]

# URL cần kiểm tra
URL = "http://estecsocson.ddns.net:81/doc/index.html#/preview"

# Trạng thái trước đó của website (ban đầu giả định website hoạt động)
last_status = "success"

def send_email(subject, body):
    """Hàm gửi email đến nhiều người nhận"""
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = ", ".join(EMAIL_RECEIVERS)  

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVERS, msg.as_string())
        server.quit()
        #print(f"📩 Đã gửi email đến: {', '.join(EMAIL_RECEIVERS)} - {subject}")
        logger.info(f"Đã gửi email đến: {', '.join(EMAIL_RECEIVERS)} - {subject}")
    except Exception as e:
        #print(f"❌ Lỗi khi gửi email: {e}")
        logger.error(f"Sending email error {e} ")

def check_website():
    """Kiểm tra trạng thái website"""
    global last_status  

    try:
        response = requests.get(URL, timeout=10)  
        if response.status_code == 200:
            #print("✅ Website hoạt động bình thường.")
            logger.info(f" Website working as normal")
            if last_status == "error":  # Nếu trước đó bị lỗi, giờ hoạt động lại thì gửi mail
                send_email("✅ Website đã hoạt động trở lại!", "Hệ thống cháy rừng tại Sóc Sơn đã có điện trở lại.")
            last_status = "success"
        else:
            error_message = f"⚠ Website gặp sự cố, hệ thống đang mất điện!"
            #print(error_message)
            logger.info(f"System have problem {error_message}")
            if last_status == "success":  # Chỉ gửi email nếu trạng thái thay đổi từ tốt → lỗi
                error_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Lấy thời gian khi sự cố xảy ra
                send_email("⚠ HỆ THỐNG GẶP SỰ CỐ!", 
                           f"Hệ thống cháy rừng đang mất điện. Lúc {error_time}, website không truy cập được.")
            last_status = "error"
    except requests.RequestException as e:
        error_message = f"❌ Website không truy cập được! Hệ thống cháy rừng mất điện"
        #print(error_message)
        logger.error(f"system have problem and cannot access")
        if last_status == "success":  # Chỉ gửi email nếu trạng thái thay đổi từ tốt → lỗi
            error_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Lấy thời gian khi sự cố xảy ra
            send_email("❌ HỆ THỐNG GẶP SỰ CỐ!", 
                       f"Hệ thống mất điện. Lúc {error_time}, không thể truy cập website. "
                       "Cách khắc phục:1. Kiểm tra lại nguồn điện 2. Kiểm tra lại modem 3. Kiểm tra lại camera 4. Kiểm tra lại server")
        last_status = "error"

if __name__ == '__main__':
    disable_quick_edit()

    #print("🕒 Script đang chạy, kiểm tra website mỗi 60 giây...")
    logger.info(f" System observing every 5 minutes")
    try:
        # Vòng lặp kiểm tra liên tục
        while True:
            check_website()  # Kiểm tra website mỗi 60 giây
            time.sleep(300)  # Chờ 60 giây rồi kiểm tra lại
    except KeyboardInterrupt:
        logger.warning("[MAIN] Interrupted by user. Exiting...")
        #print("Interrupt for exit")

    except Exception as e:
        logger.error(f"[MAIN ERROR] {e}")
        traceback.print_exc()
        time.sleep(60)
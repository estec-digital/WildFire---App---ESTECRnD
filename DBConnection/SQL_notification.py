import pyodbc, traceback
import smtplib, ctypes, multiprocessing
import datetime, logging
import time, sys
from email.mime.text import MIMEText
import json
import os

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

# Cấu hình kết nối SQL Server
server = '192.168.54.39'
database = 'WFDS'
username = 'administrator'
password = 'Pass@work1'
table = 'dbo.tbChiTietKhiTuong'
time_column = 'Thoigian'

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

# Biến trạng thái
data_lost = False

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


# Gửi email
def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = ", ".join(EMAIL_RECEIVERS)

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVERS, msg.as_string())
        server.quit()
        #print(f"[{datetime.datetime.now()}] 📩 Email đã được gửi: {subject}")
        logger.info(f"[{datetime.datetime.now()}] 📩 Email đã được gửi: {subject}")
    except Exception as e:
        # print(f"[{datetime.datetime.now()}] ❌ Lỗi gửi email: {e}")
        logger.error(f"[{datetime.datetime.now()}] ❌ Lỗi gửi email: {e}")


def disable_quick_edit():
    if sys.platform == "win32":
        import msvcrt
        kernel32 = ctypes.windll.kernel32
        hStdin = kernel32.GetStdHandle(-10)
        mode = ctypes.c_uint()
        kernel32.GetConsoleMode(hStdin, ctypes.byref(mode))
        new_mode = mode.value & ~0x0040  # Disable ENABLE_QUICK_EDIT_MODE
        kernel32.SetConsoleMode(hStdin, new_mode)

if __name__ == '__main__':
    disable_quick_edit()  # Disable quick edit mode for Windows console
    multiprocessing.freeze_support()  # for Windows support
    timeDelay = 5*60 # 5 minutes
    conn = pyodbc.connect(
            f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        )
    cursor = conn.cursor()

    now = datetime.datetime.now()
    previous_minute = (now - datetime.timedelta(minutes=1)).replace(second=0, microsecond=0)
    current_minute = now.replace(second=0, microsecond=0)

    # print(f"[{now}] ⏳ Kiểm tra dữ liệu trong khoảng: {previous_minute} đến {current_minute}")

    query = f"""
    SELECT COUNT(*) FROM {table}
    WHERE {time_column} >= ? AND {time_column} < ?
    """
    
    try:
        logger.info("[MAIN] Starting Data sensor monitoring service...")
        # Watchdog loop
        while True:
            cursor.execute(query, previous_minute, current_minute)
            count = cursor.fetchone()[0]
            if count == 0:
                if not data_lost:
                    # print(f"[{datetime.datetime.now()}] ⚠️ Không có dữ liệu lúc {previous_minute}, gửi email!")
                    logger.warning(f"[{datetime.datetime.now()}] ⚠️ Không có dữ liệu lúc {previous_minute}, gửi email!")
                    send_email(
                        "CẢNH BÁO: PLC không gửi dữ liệu",
                        f"⚠️ Không nhận được dữ liệu từ PLC trong phút: {previous_minute}.\n"
                        f"⏳ Thời gian kiểm tra: {now}\n"
                        f"🔍 Vui lòng kiểm tra hệ thống!"
                    )
                    data_lost = True
                # else:
                #     print(f"[{datetime.datetime.now()}] ⚠️ Dữ liệu vẫn chưa có, đã thông báo trước đó.")
            else:
                if data_lost:
                    # print(f"[{datetime.datetime.now()}] ✅ Dữ liệu đã có lại vào {current_minute}, gửi thông báo khôi phục.")
                    logger.warning(f"[{datetime.datetime.now()}] ❌ Lỗi kết nối SQL Server:")
                    send_email(
                        "THÔNG BÁO: PLC gửi dữ liệu trở lại",
                        f"✅ Dữ liệu đã được ghi nhận vào {current_minute}.\n"
                        f"Hệ thống hoạt động bình thường trở lại."
                    )
                    data_lost = False
            
            time.sleep(timeDelay)

    except KeyboardInterrupt:
        logger.warning("[MAIN] Interrupted by user. Exiting...")

    except Exception as e:
        logger.error(f"[MAIN ERROR] {e}")
        traceback.print_exc()
        #time.sleep(60)

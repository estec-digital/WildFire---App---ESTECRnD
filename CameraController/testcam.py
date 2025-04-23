import requests
import smtplib
import time
from email.mime.text import MIMEText
from datetime import datetime  

# Cấu hình email
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587
EMAIL_SENDER = "nguyen.hoang@biendongco.vn"
EMAIL_PASSWORD = "11235890Homehl...."

# Danh sách email người nhận
EMAIL_RECEIVERS = ["homehl872000@gmail.com", "tony.do.vh@gmail.com","quynhxm_2005@yahoo.com","hoan.vo@biendongco.vn"]

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
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVERS, msg.as_string())
        server.quit()
        print(f"📩 Đã gửi email đến: {', '.join(EMAIL_RECEIVERS)} - {subject}")
    except Exception as e:
        print(f"❌ Lỗi khi gửi email: {e}")

def check_website():
    """Kiểm tra trạng thái website"""
    global last_status  

    try:
        response = requests.get(URL, timeout=10)  
        if response.status_code == 200:
            print("✅ Website hoạt động bình thường nha baby.")
            if last_status == "error":  # Nếu trước đó bị lỗi, giờ hoạt động lại thì gửi mail
                send_email("✅ Website đã hoạt động trở lại nha baby!", "Hệ thống cháy rừng tại Sóc Sơn đã có điện trở lại nha baby, vui vẻ lên anh.")
            last_status = "success"
        else:
            error_message = f"⚠ Website gặp sự cố, hệ thống đang mất điện, em buồn quá baby ơi!"
            print(error_message)
            if last_status == "success":  # Chỉ gửi email nếu trạng thái thay đổi từ tốt → lỗi
                error_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Lấy thời gian khi sự cố xảy ra
                send_email("⚠ HỆ THỐNG GẶP SỰ CỐ! rồi baby nha", 
                           f"Hệ thống cháy rừng mất điện rồi, buồn quá huhu. Lúc {error_time}, website không truy cập được. "
                           "Đi massa không anh?")
            last_status = "error"
    except requests.RequestException as e:
        error_message = f"❌ Website không truy cập được! Hệ thống cháy rừng mất điện rồi baby ơi"
        print(error_message)
        if last_status == "success":  # Chỉ gửi email nếu trạng thái thay đổi từ tốt → lỗi
            error_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Lấy thời gian khi sự cố xảy ra
            send_email("❌ HỆ THỐNG GẶP SỰ CỐ!", 
                       f"Hệ thống mất điện rồi baby ơi, buồn quá huhu. Lúc {error_time}, không thể truy cập website. "
                       "Mong chờ anh giúp hệ thống hồi phục nha!"
                       "Cách khắc phục:1. Kiểm tra lại nguồn điện 2. Kiểm tra lại modem 3. Kiểm tra lại camera 4. Kiểm tra lại server")
        last_status = "error"

print("🕒 Script đang chạy, kiểm tra website mỗi 60 giây...")

# Vòng lặp kiểm tra liên tục
while True:
    check_website()  # Kiểm tra website mỗi 60 giây
    time.sleep(60)  # Chờ 60 giây rồi kiểm tra lại
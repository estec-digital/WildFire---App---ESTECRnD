# Lib send email
import os
import smtplib
import email
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time
import logging
import sys
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
check_email = True

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

email_timeList = []
nameList = []
prev = ""
reset_time = 0
imgNameCut = ""

def send_email(server,minutes_noti,imgName,count,kinhdo,vido,sender_email, sender_password, recipient_email_list, image_path, time_of_fire, locations_fire, station_location,nhietDo,doAm,tocDoGio,huongGio,luongMua,distance):
    try:
        #print("debug", image_path)
        global check_email
        global prev
        global reset_time
        global nameList
        global imgNameCut

        c = '('
        c_index = ([pos + 1 for pos, char in enumerate(imgName) if char == c])
        if(len(c_index) >= 1 ):
            imgNameCut  = imgName[slice(0, c_index[0]- 1)]
        else:
            imgNameCut = imgName[:-4]
            #print(imgNameCut)

        nameList.append(imgNameCut)
        #print(nameList)
        my_time = minutes_noti + 0.25
        email_timeList.append(my_time)

        if(count >= 1 and (imgNameCut == nameList[0])):
            # print("  Same Image")
            if(len(nameList) == 2):
                nameList.pop(0)
        else:
            try:
                if len(nameList) == 2:
                    nameList.pop(0)

                # print("  Email is being sent...", flush=True)
                logger.info("Starting send Email ...")

                # Tạo đối tượng email
                msg = MIMEMultipart()
                msg["From"] = sender_email
                msg["To"] = ", ".join(recipient_email_list)
                msg["Subject"] = "CẢNH BÁO CHÁY RỪNG TẠI HUYỆN SÓC SƠN - HÀ NỘI"

                with open("CanhBaoChayRung.html", "r", encoding="utf-8") as f:
                    html = f.read()

                body_text = html.format(
                    time_of_fire=time_of_fire,
                    kinhdo=kinhdo,
                    vido=vido,
                    distance=distance,
                    nhietDo=nhietDo,
                    doAm=doAm,
                    tocDoGio=tocDoGio,
                    huongGio=huongGio,
                    luongMua=luongMua,
                    fire_coordinates=f"Tọa độ đám cháy: <p><b><b>Kinh độ</b> {kinhdo}, Vĩ độ</b> {vido} </p><p> <b>Cách trạm: {distance}km </b></p> <p><b>(x={locations_fire[0]}, y={locations_fire[1]}, h={locations_fire[2]}, w={locations_fire[3]})</p></b>",
                    meteorologicalData=f"Thông tin khí tượng:<br> <b>Nhiệt độ</b> {nhietDo} <b>Độ ẩm</b> {doAm} <b>Tốc độ gió</b> {tocDoGio} <b>Hướng gió</b> {huongGio} <b>Lượng Mưa</b> {luongMua}",
                    image_path=image_path,
                    station_location=station_location
                )

                msg.attach(MIMEText(body_text, "html"))

                with open(image_path, "rb") as f:
                    image = MIMEImage(f.read())
                    image.add_header("Content-Disposition", "inline", filename=os.path.basename(image_path))
                    msg.attach(image)

                # Khởi tạo SMTP server
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(sender_email, sender_password)

                # Gửi mail
                server.sendmail(sender_email, recipient_email_list, msg.as_string())
                #server.quit()

                #print( "  " + str(datetime.now()) + "  Email sent successfully!\n")#                         ", image_path, "\n")
                logger.info("Email sent successfully!")
                # print("==========================================", flush=True)
                time.sleep(10)

            except Exception as e:
                #print( "  " + str(datetime.now()) + "  Email sending failed!\n") # image_path, "\n")
                logger.error(f" Notification.SendEmail.send_email : Email sending failed! {e}")
                # print(e)
                time.sleep(10)
                #print("==========================================", flush=True)
                pass

    except Exception as e:
        #print(e)
        logger.error(f" Notification.SendEmail.send_email: {e}")
        pass


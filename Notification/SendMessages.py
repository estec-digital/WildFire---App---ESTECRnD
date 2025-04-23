import time
import threading
import requests
import random
# Download the helper library from https://www.twilio.com/docs/python/install
from twilio.rest import Client
import logging, os, sys
from datetime import datetime,timedelta
check_tele = True
check_sms = True

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


tele_timeList = []
sms_timeList = []
tele_waitingTime = ""
sms_waitingTime = ""
imgNameCut = ""
nameList=[]
temp = 0
def send_tele_msg(minutes_noti,count,delay,TELEGRAM_CHATID,TELEGRAM_TOKEN,imgName):
   try:
        global tele_waitingTime
        global imgNameCut
        global temp
        c = '('
        c_index = ([pos + 1 for pos, char in enumerate(imgName) if char == c])

        if (len(c_index) >= 1):
            imgNameCut = imgName[slice(0, c_index[0] - 1)]
        else:
            imgNameCut = imgName[:-4]
            #print(imgNameCut)
            logger.info(imgNameCut)

        nameList.append(imgNameCut)
        minute = datetime.now().minute
        if(count <= 1 ):
            temp = minute - 1
        tele_waitingTime = temp + 1


        if(len(tele_timeList) == 0):
            tele_timeList.append(tele_waitingTime)

        # print(tele_timeList)
        # print(nameList)
        logger.info(nameList, tele_timeList)
        if (count >= 1 and (minute < tele_timeList[0])):
            #print("TeleSender is in waiting list")
            logger.info("TeleSender is in waiting list")
            if (len(nameList) == 2):
                nameList.pop(0)

        elif(imgNameCut == nameList[0]):
            #print("Same Image")
            logger.info("Same Image")
            if (len(nameList) == 2):
                nameList.pop(0)
        else:
            if (len(nameList) == 2):
                nameList.pop(0)
            #print("Tele message is being Send")
            logger.info("Tele message is being Send")
            a = round(random.random(), 2)
            b = round(random.random(), 2)
            c = round(random.random(), 2)
            warning_message = ("Trạm báo cháy: " + str(a)
                               + "\nThời gian: " + str(b)
                               + "\nDiện tích cháy: " + str(c)
                               + "\n\nHướng dẫn xử lý:"
                               + "\n- Giữ bình tĩnh, không hoảng loạn."
                               + "\n- Di chuyển ra khỏi khu vực cháy rừng."
                               + "\n- Nếu bị mắc kẹt, tìm nơi an toàn để trú ẩn."
                               + "\n- Gọi điện thoại đến hotline để báo cháy."
                               + "\n\nLiên hệ: 080808080808")
            url_req = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage" + "?chat_id=" + TELEGRAM_CHATID + "&text=" + warning_message
            results = requests.get(url_req)
            # print(results.json())
            # print("Sending Tele successfully")
            logger.info("Sending Tele successfully")

            #reset
            if (len(tele_timeList) == 1):
                temp = tele_timeList[0]
                tele_timeList.clear()

   except Exception as e:
        #print("Sending Tele fail")
        logger.error(e)
        #print(e)

def send_sms_msg(minutes_noti,count,delay,sender,receiver,SMS_ACCOUNT_SID,SMS_AUTH_TOKEN,imgName):
    try:
        global sms_waitingTime
        global imgNameCut
        global temp
        c = '('
        c_index = ([pos + 1 for pos, char in enumerate(imgName) if char == c])
        #print(c_index)
        if (len(c_index) >= 1):
            imgNameCut = imgName[slice(0, c_index[0] - 1)]
        else:
            imgNameCut = imgName[:-4]
            #print(imgNameCut)

        nameList.append(imgNameCut)
        minute = datetime.now().minute
        if (count <= 1):
            temp = minute - 1

        sms_waitingTime = temp + 1

        if (len(sms_timeList) == 0):
            sms_timeList.append(sms_waitingTime)
        #print(sms_timeList)

        #print(nameList)
        if (count >= 1 and (minute < sms_timeList[0])):
            #print("TeleSender is in waiting list")
            if (len(nameList) == 2):
                nameList.pop(0)

        elif (imgNameCut == nameList[0]):
            #print("Same Image")
            if (len(nameList) == 2):
                nameList.pop(0)
        else:
            # Find your Account SID and Auth Token at twilio.com/console
            # and set the environment variables. See http://twil.io/secure
            a = round(random.random(), 2)
            b = round(random.random(), 2)
            c = round(random.random(), 2)
            account_sid = SMS_ACCOUNT_SID
            auth_token = SMS_AUTH_TOKEN
            client = Client(account_sid, auth_token)
            # warning_message = ("Trạm báo cháy: " + str(a)
            #                    + "\nThời gian: " + str(b)
            #                    + "\nDiện tích cháy: " + str(c)
            #                    + "\n\nHướng dẫn xử lý:"
            #                    + "\n- Giữ bình tĩnh, không hoảng loạn."
            #                    + "\n- Di chuyển ra khỏi khu vực cháy rừng."
            #                    + "\n- Nếu bị mắc kẹt, tìm nơi an toàn để trú ẩn."
            #                    + "\n- Gọi điện thoại đến hotline để báo cháy."
            #                    + "\n\nLiên hệ: 080808080808")
            warning_message = "Có cháy!"
            message = client.messages \
                .create(
                body=warning_message,
                from_=f'{sender}',
                # +84393059097
                to=f'{receiver}'
            )
            #print(message.sid)
            #print("Sending SMS successfully")
            # reset
            if (len(sms_timeList) == 1):
                temp = sms_timeList[0]
                sms_timeList.clear()
    except Exception as e:
        #print("Sending SMS fail")
        logger.error(e)
        #print(f'SMS error: {e}')



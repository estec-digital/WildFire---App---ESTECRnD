# -*- coding: utf-8 -*-
import _thread
import math
import time
import multiprocessing
from PIL import Image as PImage
import pandas as pd
from DBConnection.ConnectSQL import checkconection
from ImagesDetector.CalculateFirePosition import calculateDistance, calDistance
from ImagesDetector.GetDateTimeCapturing import capturingDate
from DBConnection import ConnectSQL
from ImagesDetector.GetImageInfo import getDate
from UserInput import InputEmailSendReceive as IES
import logging
from ImagesDetector.SaveImage import save
from Notification import SendEmail,SendMessages
from Notification.helper_send_email import send_email_wrapper
import threading, os
import sys, json
from datetime import datetime, timedelta

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

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

defList = []
distanceList =[]
avg = 0
sum = 0
count = 1

def insertSQL_tbDamChay(df,image,saveFolder,imageName,confidence):
    try:
        path = saveFolder + "\\" + imageName

        xmin = int(df.iloc[0, 0])
        ymin = int(df.iloc[0, 1])
        xmax = int(df.iloc[0, 2])
        ymax = int(df.iloc[0, 3])
        #print(f"{xmin}, {xmax}, {ymin}, {ymax}")
        X = (xmax + xmin) / 2
        Y = (ymax + ymin) / 2
        W = xmax - xmin
        H = ymax - ymin
        DuongKinhDC = W * 0.012 #tiletuongdoi
        RealHeight = H * 0.012

        location_fire=[X,Y,H,W]
        TiLe = f" Accuracy:  {str(round(confidence))}%"
        c, d = '_', '.'
        c_index = ([pos + 1 for pos, char in enumerate(imageName) if char == c])
        capturing_date, query_KhiTuong_Date = getDate(image)

        #print(f"{capturing_date, query_KhiTuong_Date}")

        if( len(c_index) >= 7):
            MaTram = imageName[slice(c_index[0], c_index[1] - 1)]

            GocNgang = round(float(imageName[slice(c_index[4], c_index[5] - 1)]))
            GocDung = round(float(imageName[slice(c_index[6], c_index[7] - 1)]))
            DoPhongDai = imageName[:-4][c_index[8]:]

            DoPhongDai = round(float(DoPhongDai[:1]))
            ViTri = "1"
            img = PImage.open(path)
            RongAnh = img.width

            CaoAnh = img.height
            #SocSon CameraGPS
            camera_lat = 21.2785847977784
            camera_lon = 105.815950208633
            #bug fround - 24-12-2024
            kdc, vdc , caoc, docc, hdocc = calculatePos(GocNgang, DoPhongDai, X, W, ViTri, RongAnh, CaoAnh, Y, H, camera_lon, camera_lat)

            searchDistance = calculateKDVDC(xmin,xmax,ymin,ymax,camera_lon,camera_lat)

            #convertSearchDistnacec to Distance
            distance = distanceMean(searchDistance,imageName) / 10

            meteorologicalDataQuery = f"select NhietDo,DoAm,TocDoGio,HuongGio,LuongMua from tbChiTietKhiTuong where ThoiGian = '{str(query_KhiTuong_Date)}';"
            meteorologicalData = pd.read_sql(meteorologicalDataQuery, checkconection())
            #print("----Check meteorologicalData----")
            #print(meteorologicalData)
            if(meteorologicalData.empty):
                nhietDo = "Không có dữ liệu"
                doAm = 0
                tocDoGio = 0
                huongGio = 0
                luongMua = "Không có dữ liệu"
            else:
                nhietDo = meteorologicalData.NhietDo[0]
                doAm = meteorologicalData.DoAm[0]
                tocDoGio = meteorologicalData.TocDoGio[0]
                huongGio = meteorologicalData.HuongGio[0]
                luongMua = meteorologicalData.LuongMua[0]

            infoList = [capturing_date, MaTram, ViTri, int(round(X)), int(round(Y)), W, H, imageName, int(GocNgang),
                        int(GocDung), int(DoPhongDai), RongAnh, CaoAnh, DuongKinhDC, kdc, vdc, caoc, docc, hdocc, TiLe]
            
            ConnectSQL.insertData("tbDamChay", infoList)

    except Exception as e:
        #print(e)
        logger.error(f"insertSQL_tbDamChay: {e}")
        #print(" Something wrong with insert SQL tbDamChay")
        pass

def send_email_Damchay(server,minutes_noti,count,df,image,saveFolder,imageName,confidence,
                       sender_email,sender_password, input_json_path):
    
    with open(input_json_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    notification_periods = config.get("Notification_period", [])
    period = notification_periods[0]
    start_hour = int(period.get("start", 0))
    end_hour = int(period.get("end", 23))


    if start_hour <= datetime.now().hour <= end_hour:
        try:
            path = saveFolder + "\\" + imageName

            # Thông tin tài khoản email của bạn
            sender_email = sender_email
            sender_password = sender_password
            # Thông tin người nhận
            with open(input_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                sender_email = data.get("Email_sender")
                sender_password = data.get("Email_password")
                recipient_email_list = data.get("Email_receivers", [])

            if recipient_email_list == []:
                logger.error(" No recipient email found")
                return None

            xmin = int(df.iloc[0, 0])
            ymin = int(df.iloc[0, 1])
            xmax = int(df.iloc[0, 2])
            ymax = int(df.iloc[0, 3])
            #print(f"{xmin}, {xmax}, {ymin}, {ymax}")
            X = (xmax + xmin) / 2
            Y = (ymax + ymin) / 2
            W = xmax - xmin
            H = ymax - ymin
            DuongKinhDC = W * 0.012 #tiletuongdoi
            RealHeight = H * 0.012

            location_fire=[X,Y,H,W]
            TiLe = f" Accuracy:  {str(round(confidence))}%"
            c, d = '_', '.'
            c_index = ([pos + 1 for pos, char in enumerate(imageName) if char == c])
            capturing_date, query_KhiTuong_Date = getDate(image)

            #print(f"{capturing_date, query_KhiTuong_Date}")

            if( len(c_index) >= 7):
                MaTram = imageName[slice(c_index[0], c_index[1] - 1)]

                GocNgang = round(float(imageName[slice(c_index[4], c_index[5] - 1)]))
                GocDung = round(float(imageName[slice(c_index[6], c_index[7] - 1)]))
                DoPhongDai = imageName[:-4][c_index[8]:]

                DoPhongDai = round(float(DoPhongDai[:1]))
                ViTri = "1"
                #logger.info(f" AI result Image path: {path}")
                img = PImage.open(path)
                RongAnh = img.width
                CaoAnh = img.height
                #SocSon CameraGPS
                camera_lat = 21.2785847977784
                camera_lon = 105.815950208633
                #bug fround - 24-12-2024
                kdc, vdc , caoc, docc, hdocc = calculatePos(GocNgang, DoPhongDai, X, W, ViTri, RongAnh, CaoAnh, Y, H, camera_lon, camera_lat)

                searchDistance = calculateKDVDC(xmin,xmax,ymin,ymax,camera_lon,camera_lat)

                #convertSearchDistnacec to Distance
                distance = distanceMean(searchDistance,imageName) / 10

                meteorologicalDataQuery = f"select NhietDo,DoAm,TocDoGio,HuongGio,LuongMua from tbChiTietKhiTuong where ThoiGian = '{str(query_KhiTuong_Date)}';"
                meteorologicalData = pd.read_sql(meteorologicalDataQuery, checkconection())
                #print("----Check meteorologicalData----")
                #print(meteorologicalData)
                if(meteorologicalData.empty):
                    nhietDo = "Không có dữ liệu"
                    doAm = 0
                    tocDoGio = 0
                    huongGio = 0
                    luongMua = "Không có dữ liệu"
                else:
                    nhietDo = meteorologicalData.NhietDo[0]
                    doAm = meteorologicalData.DoAm[0]
                    tocDoGio = meteorologicalData.TocDoGio[0]
                    huongGio = meteorologicalData.HuongGio[0]
                    luongMua = meteorologicalData.LuongMua[0]

                infoList = [capturing_date, MaTram, ViTri, int(round(X)), int(round(Y)), W, H, imageName, int(GocNgang),
                            int(GocDung), int(DoPhongDai), RongAnh, CaoAnh, DuongKinhDC, kdc, vdc, caoc, docc, hdocc, TiLe]
            
                if W > 60 and H > 60 and H < 950 and Y < 800:
                    path = os.path.join(saveFolder, imageName)
                    if os.path.exists(path):
                        thread_send_email = threading.Thread(target=SendEmail.send_email,args=(
                            server, minutes_noti, imageName, count, kdc, vdc,
                            sender_email, sender_password, recipient_email_list,
                            path, capturing_date, location_fire, MaTram,
                            nhietDo, doAm, tocDoGio, huongGio, luongMua, distance
                        ))
                        thread_send_email.daemon = True
                        thread_send_email.start()
                        
        except Exception as e:
            logger.error(f"Error send email Damchay: {e}")
            pass
    else:
        logger.info(f"Email sending time is out of range time send: {start_hour} - {end_hour} hours")
        return None


def calculatePos(goc, dophongdai1,x1,w1,vitri,ronganh1,caoanh1,y1,h1, kd1,vd1):
    try:
        vitri1 = (goc / 15 ) -1
        gocngang1 = vitri1*15,
        gocdung1 = 90
        if (dophongdai1 < 10):
           gocanh1 = 54.5
        elif(dophongdai1 >= 10 and dophongdai1  < 30):
            gocanh1 = 369.78048*(math.pow(dophongdai1*1.0000, (-0.82958)))
        elif(dophongdai1 > 90 and dophongdai1<300):
            gocanh1 = 138.18748*(math.pow(dophongdai1*1.0000,(-0.66719)))
        elif(dophongdai1 >= 300):
            gocanh1 = 3
        xgiuadc1 = x1 + w1 / 2
        yduoidc1 =y1 + h1
        gocngang1 =  vitri * 15
        gocngangdc1 = float(gocngang1) - float(gocanh1 / 2) + float(gocanh1) * float(xgiuadc1) / float(ronganh1)
        gocngangdc1 = gocngangdc1+ 15
        gocdungdc1 = float(gocdung1) + float(caoanh1/ 2) * float(gocanh1) / float(ronganh1) - float(yduoidc1) * float(gocanh1) /float(ronganh1)
        cos1 = math.sin((goc) * 3.1416 / 180)
        sin1 = math.cos((goc) * 3.1416 / 180)
        caodiahinh1 = 100.1
        caongam1 = 200.1

        if (vd1 > 20.6):
            query = f"SELECT cao from DiaHinhRungChuRung WHERE abs({float(kd1)} -kd)<0.18 and abs({float(vd1)}-vd)<0.18;"
            caotram1 = pd.read_sql(query, checkconection())

            caotram1 = caotram1["cao"].values[-1]

        elif (vd1 > 19.2 and vd1 < 20.6):
            query = f"SELECT cao from DiaHinhRungChuRung where abs({float(kd1)}-kd)<0.20 and abs({float(vd1)}-vd)<0.20;"
            caotram1 = pd.read_sql(query, checkconection())
            caotram1 = caotram1["cao"].values[-1]

        caotram1 = caotram1 + 18

        gocngam1 = gocdungdc1 - 90
        i = 1
        n = 1
        while(i <= 100 and caongam1 >= caodiahinh1):
            kddc1 = kd1 + i * cos1 * 0.000900901
            vddc1 = vd1 + i * sin1 * 0.000900901
            if (vd1 > 20.6):
                query = f"select id, cao , doc, hdoc from DiaHinhRungChuRung where abs({kddc1}-kd)<0.15 and abs({vddc1}-vd)<0.15;"
                test = pd.read_sql(query, checkconection())
                caodiahinh1 = test["cao"].values[0]
                docdiahinh1 = test["doc"].values[0]
                hdocdiahinh1 = test["hdoc"].values[0]
            if(hdocdiahinh1<0):
                hdocdiahinh1 = 0
            caongam1 = caotram1 +math.sin(gocngam1*3.1416/180)*n*100
            i = i + 1
            n = n+1
            #print ("Kinh Do Chay :"+ str(kddc1) +"\nVi Do Chay: " + str(vddc1))

            return kddc1,vddc1,caodiahinh1,docdiahinh1,hdocdiahinh1
    except Exception as  e:
        logger.error(f"ImagesDetector.InsertData.calculatePos: {e}")



def calculateKDVDC(xmin,xmax,ymin,ymax,kd1,vd1):
    try:
        chieuRong_anh = 2550
        chieuCao_anh = 1440
        #Horizontal field of view: 55° to 2.4° (wide-tele),

        # Vertical field of view: 33° to 1.4° (wide-tele),
        #
        # Diagonal field of view: 61.5° to 2.8° (wide-tele)
        fov_vec = 61.5
        caoChanTram = ''
        fov_each_pixel = fov_vec / chieuCao_anh
        do_xmin_x = (chieuRong_anh/2 - xmin) * fov_each_pixel
        do_xmin_y = (chieuCao_anh/2 - ymin) * fov_each_pixel
        #newDigit = ymax - (ymax % 10) / 2
        chieuCaoToiDay = chieuCao_anh/2 - ymax
        doChieuCaoToiDay = chieuCaoToiDay * fov_each_pixel

        #calculate kdc, vdc for distance from object to camera is 1.2km
        if (vd1 > 20.6):
            query = f"SELECT cao from DiaHinhRungChuRung WHERE abs({float(kd1)} -kd)<0.18 and abs({float(vd1)}-vd)<0.18;"
            caoChanTram = pd.read_sql(query, checkconection())
            caoChanTram = caoChanTram["cao"].values[-1]

        elif (vd1 > 19.2 and vd1 < 20.6):
            query = f"SELECT cao from DiaHinhRungChuRung where abs({float(kd1)}-kd)<0.20 and abs({float(vd1)}-vd)<0.20;"
            caoChanTram = pd.read_sql(query, checkconection())
            caoChanTram = caoChanTram["cao"].values[-1]

        caotram = caoChanTram + 18
        #print(f"cao tram: {caotram}")
        for searchDistance in range(1,300):
            doCao = abs(searchDistance  * math.tan(doChieuCaoToiDay) + caotram)
            #print(f"{searchDistance} ~= 1.2km, Docao = {doCao}")

            if(doCao >= 55):
                #print(f"special {searchDistance} ~= 1.2km, Docao = {doCao}")
                return searchDistance if (searchDistance < 25) else 11

    except Exception as e:
        logger.error(f"ImagesDetector.InsertData.calculateKDVDC: {e}")


def distanceMean(searchDistance, imageName):
    global defList
    global distanceList
    global avg
    global sum
    global count

    c = '('
    c_index = ([pos + 1 for pos, char in enumerate(imageName) if char == c])
    if (len(c_index) >= 1):
        imgNameCut = imageName[slice(0, c_index[0] - 1)]
    else:
        imgNameCut = imageName[:-4]
    defList.append(imgNameCut)
    if (searchDistance == None):
        searchDistance = 0
    distanceList.append(searchDistance)

    if len(defList) == 0:
        logger.error("ImagesDetector.InsertData.distanceMean: no image")

    elif len(c_index) >= 1 and f"{imageName[:-7]}" != defList[0]:
        #print("new Image found")
        defList = [defList[-1]]  # giữ lại 1 phần tử cuối
        distanceList = [distanceList[-1]]
        count = 1
        return 11

    elif len(c_index) == 0 and f"{imageName[:-4]}" != defList[0]:
        #print("new Image found")
        defList = [defList[-1]]
        distanceList = [distanceList[-1]]
        count = 1
        return 11

    else:
        sum_distance = 0
        count = 0
        for i in range(len(distanceList)):
            try:
                dist = int(distanceList[i])
                if dist < 10:
                    dist = 11  # gán mặc định
                sum_distance += dist
                distanceList[i] = dist
                count += 1
            except Exception as e:
                logger.error(f"ImagesDetector.InsertData.distanceMean: Distance parse failed: {e}")
        
        return min(distanceList) if len(distanceList) > 1 else 11

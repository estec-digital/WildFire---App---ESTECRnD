import _thread
import time, json 
from datetime import datetime
import numpy as np
import pandas as pd
import pyodbc
from UserInput.InputDB import db
import logging
import urllib, os
import warnings
import sys, random
from dateutil import parser

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy")

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

global checkInsertion
khi_tuong_tong_hop_default = 0
checkTime = []
column = ["ThoiGian", "MaTram","ViTri","X","Y", "W", "H", "Anh" ,"GocNgang","GocDung", "DoPhongDai","RongAnh","CaoAnh","DuongKinhDC","kdc","vdc","caoc","docc","hdocc","TiLe"]
nguycochay_column = ["Id","NhietDo", "DoAm","TocDoGio","HuongGio","LuongMua","ThoiGian","KHTram", "MaTram","P","NguyCo"]

# Global DB config variables
SERVER = "192.168.54.39" #None
USERNAME = "administrator" #None
PASSWORD = "Pass@work1" #None
DATABASE = "WFDS"#None

def configure_db(server, username, password, database):
    global SERVER, USERNAME, PASSWORD, DATABASE
    SERVER = server
    USERNAME = username
    PASSWORD = password
    DATABASE = database
    logger.info(f"[DB CONFIG] Database configured: {DATABASE} on {SERVER}")

def checkconection():
    try:
        conectionString = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}'
        conn = pyodbc.connect(conectionString)
        return conn
    except Exception as e:
        #print("\n\n SQL Connection Fail - ConnectSQL.checkconection  \n\n") #Kết nối thất bại")
        #logger.error(f" SQL Connect failed DBConnection.ConnectSQL.checkconnection ")#: {e}")
        #print(e)
        return None
        
def createTable():
    try:
        conn = checkconection()
        cursor = conn.cursor()
        SQL_QUERY = ('''
                        CREATE TABLE tbDamChay(
                            ID int NOT NULL  IDENTITY(1,1) PRIMARY KEY,
                            ThoiGian datetime,
                            MaTram nvarchar(50),
                            ViTri nvarchar(50),
                            X int,
                            Y int,
                            W int,
                            H int,
                            Anh nvarchar(max),
                            GocNgang int,
                            GocDung int,
                            DoPhongDai int,
                            RongAnh int,
                            CaoAnh int,
                            DuongKinhDC float,
                            kdc float,
                            vdc float, 
                            caoc float, 
                            docc float,
                            hdocc float,
                            TiLe nvarchar(50)
                        );
                    ''')
        cursor.execute(SQL_QUERY)
        conn.commit()
        #conn.close()
        logger.info("Table created successful")
    except:
        logger.info("Table exist")

def selectMaTram(table_name):
    try:
        conn = checkconection()
        SQL_QUERY = f"SELECT MaTram from {table_name}"
        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        dataList = cursor.fetchall()
        #conn.close()
        return dataList
    except Exception as e:
        logger.error(e)

def selectKHTram(table_name):
    try:
        conn = checkconection()
        SQL_QUERY = f"SELECT KHTram from {table_name}"
        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        dataList = cursor.fetchall()
        #conn.close()
        return dataList
    except Exception as e:
        logger.error(e)
        #print(e)

def selectCapDate(table_name,image_name):
    try:
        conn = checkconection()
        SQL_QUERY = f"SELECT Image_time from {table_name} WHERE(Image_name = '{image_name}');"
        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        dataList = cursor.fetchall()
        #conn.close()
        return str(dataList[0])
    except Exception as e:
        logger.error(e)

def insertKhiTuong1h(table_name, parameters):
    try:
        conn = checkconection()
        if conn:
            cursor = conn.cursor()
            # Do your DB logic
            merge_query = f"""
            MERGE {table_name} AS target
            USING (SELECT ? AS ThoiGian, ? AS MaTram) AS source
            ON (target.ThoiGian = source.ThoiGian AND target.MaTram = source.MaTram)
            WHEN MATCHED THEN 
                UPDATE SET
                    {nguycochay_column[1]} = ?,  -- NhietDo
                    {nguycochay_column[2]} = ?,  -- DoAm
                    {nguycochay_column[3]} = ?,  -- TocDoGio
                    {nguycochay_column[4]} = ?,  -- HuongGio
                    {nguycochay_column[5]} = ?,  -- LuongMua
                    {nguycochay_column[9]} = ?,  -- P
                    {nguycochay_column[10]} = ?  -- NguyCo
            WHEN NOT MATCHED THEN
                INSERT ({','.join(nguycochay_column)})
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """

            cursor.execute(merge_query, (
                parameters[6], parameters[8],  # source: ThoiGian, MaTram
                parameters[1], parameters[2], parameters[3], parameters[4], parameters[5],
                parameters[9], parameters[10],  # update values
                *parameters  # insert values
            ))

            conn.commit()
            #conn.close()
            #logger.info("[DONE] insert khi tuong 1h")
        else:
            logger.error("[CRITICAL] Could not establish DB connection. Skipping operation.")
        #cursor = conn.cursor()
        #logger.info(f"[UPSERT] {parameters[6]} | MaTram={parameters[8]}")

    except Exception as e:
        logger.error(f"[DB ERROR] insertNguyCoChay (MERGE): {e}")


def insertNguyCoChay_skip_update(table_name, parameters):
    try:
        conn = checkconection()
        cursor = conn.cursor()

        # Check if a record already exists for the same ThoiGian and MaTram
        check_query = f"""
            SELECT COUNT(*) FROM {table_name}
            WHERE ThoiGian = ? AND MaTram = ?
        """
        cursor.execute(check_query, (parameters[6], parameters[8]))  # ThoiGian, MaTram
        existing_count = cursor.fetchone()[0]

        if existing_count == 0:
            SQL_QUERY = (
                f"INSERT INTO {table_name} ({nguycochay_column[0]},{nguycochay_column[1]},{nguycochay_column[2]},"
                f"{nguycochay_column[3]},{nguycochay_column[4]},{nguycochay_column[5]},{nguycochay_column[6]},"
                f"{nguycochay_column[7]},{nguycochay_column[8]},{nguycochay_column[9]},{nguycochay_column[10]}) "
                f"VALUES (?,?,?,?,?,?,?,?,?,?,?)"
            )
            cursor.execute(SQL_QUERY, parameters)
            conn.commit()
            logger.info(f"[INSERTED] Fire risk for {parameters[6]} (MaTram={parameters[8]})")
        else:
            logger.info(f"[SKIPPED] Already exists: ThoiGian={parameters[6]}, MaTram={parameters[8]}")

        #conn.close()

    except Exception as e:
        logger.error(f"[DB ERROR] insertNguyCoChay: {e}")


def selectNhietDo(table_name):
    try:
        conn = checkconection()
        SQL_QUERY = f"SELECT NhietDo from {table_name}"
        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        dataList = cursor.fetchall()
        #conn.close()
        return dataList
    except Exception as e:
        logger.error(e)
        #print(e)

def selectDoAm(table_name):
    try:
        conn = checkconection()
        SQL_QUERY = f"SELECT DoAM from {table_name}"
        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        dataList = cursor.fetchall()
        #conn.close()
        return dataList
    except Exception as e:
        logger.error(e)

def deleteRecord():
    try:
        conn = checkconection()
        cursor = conn.cursor()
        cursor.execute(f'''
                DELETE FROM tbChiTietKhiTuong1h 
               ''')

        conn.commit()
        #conn.close()
    except Exception as e:
        logger.error(e)

#createNgNhanTable()
def selectLuongMua(table_name):
    try:
        conn = checkconection()
        SQL_QUERY = f"SELECT LuongMua from {table_name}"
        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        dataList = cursor.fetchall()
        #conn.close()
        return dataList
    except Exception as e:
        logger.error(e)
        #print(e)

def selectAll(table_name):
    try:
        conn = checkconection()
        SQL_QUERY = f"SELECT * from {table_name}"
        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        dataList = cursor.fetchall()
        #conn.close()
        return dataList
    except Exception as e:
        logger.error(e)
        #print(e)

def convertKhiTuong(KhiTuongTongHop):
    if (KhiTuongTongHop < 2000):
        level = "I"
    elif (2000 <= KhiTuongTongHop <= 4000):
        level = "II"
    elif (4001 < KhiTuongTongHop <= 7000):
        level = "III"
    elif (7001 < KhiTuongTongHop <= 10000):
        level = "IV"
    elif (KhiTuongTongHop > 10000):
        level = "V"
    else:
        level = "Unavailable"
    return level

def calculateRisk(LuongMua, KhiTuongTruoc, NhietDoKK , DoAm):

    if (LuongMua >= 7):
        K = 0
        KhiTuongTongHop = K * (  KhiTuongTruoc +  NhietDoKK * DoAm)
        if (KhiTuongTongHop < 2000):
            level = "I"
        elif (2000 <= KhiTuongTongHop <= 4000):
            level = "II"
        elif (4001 < KhiTuongTongHop <= 7000):
            level = "III"
        elif (7001 < KhiTuongTongHop <= 10000):
            level = "IV"
        else:
            level = "V"

        return level, KhiTuongTongHop
    elif(LuongMua < 7):
        K = ( 7 - LuongMua ) / 7
        KhiTuongTongHop = K * ( KhiTuongTruoc +  NhietDoKK * DoAm)
        if (KhiTuongTongHop < 2000):
            level = "I"
        elif (2000 <= KhiTuongTongHop <= 4000):
            level = "II"
        elif (4001 < KhiTuongTongHop <= 7000):
            level = "III"
        elif (7001 < KhiTuongTongHop <= 10000):
            level = "IV"
        else:
            level = "V"
        return level, KhiTuongTongHop

def fixCalculateRisk(kqKhiTuong,LuongMua):
    if(LuongMua < 7):
        K = (7 - LuongMua) / 7
        KhiTuongTongHop = K * kqKhiTuong

        if (KhiTuongTongHop < 2000):
            level = "I"
        elif (2000 <= KhiTuongTongHop <= 4000):
            level = "II"
        elif (4001 < KhiTuongTongHop <= 7000):
            level = "III"
        elif (7001 < KhiTuongTongHop <= 10000):
            level = "IV"
        else:
            level = "V"
        return level,KhiTuongTongHop
    else:
        K = 0
        KhiTuongTongHop = K * kqKhiTuong

        if (KhiTuongTongHop < 2000):
            level = "I"
        elif (2000 <= KhiTuongTongHop <= 4000):
            level = "II"
        elif (4001 < KhiTuongTongHop <= 7000):
            level = "III"
        elif (7001 < KhiTuongTongHop <= 10000):
            level = "IV"
        else:
            level = "V"
        return level, KhiTuongTongHop

def DataSensorCheck(input_json_path):
    try:
        global khi_tuong_ngay_hom_truoc
        khi_tuong_tong_hop_default = 0
        query = '''WITH ThoiGianTron AS (
                    SELECT  
                        AVG(NhietDo) AS NhietDo, 
                        AVG(DoAm) AS DoAm, 
                        MAX(TocDoGio) AS TocDoGio,
                        MAX(HuongGio) AS HuongGio,
                        AVG(LuongMua) AS LuongMua,
                        DATEADD(HOUR, DATEDIFF(HOUR, 0, ThoiGian), 0) AS ThoiGian,
                        'SocSon' AS KHTram,
                        2 AS MaTram
                    FROM tbChiTietKhiTuong
                    WHERE KHTram = 'SocSon'
                    GROUP BY DATEADD(HOUR, DATEDIFF(HOUR, 0, ThoiGian), 0)
                )
                SELECT 
                    ROW_NUMBER() OVER (ORDER BY ThoiGian DESC) AS Id,  
                    NhietDo, 
                    DoAm, 
                    TocDoGio, 
                    HuongGio, 
                    LuongMua, 
                    ThoiGian, 
                    KHTram, 
                    MaTram
                FROM ThoiGianTron
                ORDER BY ThoiGian DESC;
                '''
        # query = '''WITH ThoiGianTron AS (
        #     SELECT  
        #         AVG(NhietDo) AS NhietDo, 
        #         AVG(DoAm) AS DoAm, 
        #         MAX(TocDoGio) AS TocDoGio,
        #         MAX(HuongGio) AS HuongGio,
        #         AVG(LuongMua) AS LuongMua,
        #         DATEADD(HOUR, DATEDIFF(HOUR, 0, ThoiGian), 0) AS ThoiGianRounded,
        #         'SocSon' AS KHTram,
        #         2 AS MaTram
        #     FROM tbChiTietKhiTuong
        #     WHERE KHTram = 'SocSon'
        #     GROUP BY DATEADD(HOUR, DATEDIFF(HOUR, 0, ThoiGian), 0)
        # )

        # SELECT 
        #     ROW_NUMBER() OVER (ORDER BY ThoiGianRounded DESC) AS Id,  
        #     NhietDo, 
        #     DoAm, 
        #     TocDoGio, 
        #     HuongGio, 
        #     LuongMua, 
        #     ThoiGianRounded AS ThoiGian,
        #     KHTram, 
        #     MaTram
        # FROM ThoiGianTron
        # ORDER BY ThoiGianRounded DESC;
        # '''
        df = pd.read_sql(query, checkconection())
        with open(input_json_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        bang_tra_do_am_path = config.get("Bang_tra_do_am")
        bang_tra_do_am = pd.read_csv(bang_tra_do_am_path, encoding="utf-8")
        
        df.set_index(df["Id"], inplace= True)
        df.sort_values(by='ThoiGian',ascending=True,inplace=True)

        DateTimeExtractList = pd.to_datetime(df['ThoiGian']).dt.floor('D')
        getDateList = DateTimeExtractList.drop_duplicates()
        getDateValues = getDateList.values
        special_time_list = []

        m=0
        khi_tuong_ngay_hom_truoc = 0
        sum = 0
        sumLuongMuaList = []
        firstHoursList = ["13","14","15","16","17","18","19","20","21","22","23"]
        #df["NhietDo"] = df["NhietDo"] - 6
        df["NhietDo"] = df["NhietDo"].round(decimals=1)
        df['AtLuongMua'] = abs(df['LuongMua'].shift(1) - df['LuongMua'])
        #df["DoAm"] = df["DoAm"] + ((30 * df["DoAm"]) / 100)
        df["DoAm"] = df["DoAm"].round(decimals=1)

        # If you want to ignore the first row (since it has no previous row), you can drop it:
        df = df.dropna(subset=['AtLuongMua'])
        #print(f"Datetime: {DateTimeExtractList}")

        for j in range(len(set(DateTimeExtractList))):

            special_time = df.loc[
                (df['ThoiGian'] == f"{str(getDateValues[j])[:10]} 13:00:00") & (df['KHTram'] == "SocSon")]
            special_time_list.append(special_time)
            #print("khi_tuong_ngay_hom_truoc: " + str(khi_tuong_ngay_hom_truoc))

            selected_first_time = df.loc[
                ((df['ThoiGian'] >= f"{str(getDateValues[j])[:10]} {firstHoursList[m]}:00:00")) &
                ((df['ThoiGian'] <= f"{str(getDateValues[j])[:10]} 23:00:00"))]
            selected = df.loc[((df['ThoiGian'] >= f"{str(getDateValues[j])[:10]} 00:00:00")) & (
            (df['ThoiGian'] < f"{str(getDateValues[j])[:10]} 13:00:00"))]
            ids = df.index[((df['ThoiGian'] >= f"{str(getDateValues[j])[:10]} {firstHoursList[m]}:00:00")) &
                ((df['ThoiGian'] <= f"{str(getDateValues[j])[:10]} 23:00:00"))].tolist()
            next_ids = df.index[((df['ThoiGian'] >= f"{str(getDateValues[j])[:10]} 00:00:00")) & (
            (df['ThoiGian'] < f"{str(getDateValues[j])[:10]} 13:00:00"))].tolist()

            if (len(selected["LuongMua"].values) > 0):
                #deleteRecord()
                for k in range(len(selected["LuongMua"].values)):

                    if (selected.empty):
                        pass
                    if (special_time.empty):
                        pass
                    #Prior 13h
                    if (selected["AtLuongMua"].values[k] == 0):
                        if (sum < 7):
                            khi_tuong_tong_hop = khi_tuong_ngay_hom_truoc * (( 7 - sum ) / 7)
                            next_nguy_co_chay_rung = convertKhiTuong(khi_tuong_tong_hop)
                        elif (sum > 7):
                            khi_tuong_tong_hop = khi_tuong_ngay_hom_truoc * 0
                            next_nguy_co_chay_rung = convertKhiTuong(khi_tuong_tong_hop)
                    #Afterward
                    else:
                        # print("DoHutBaoHoa: " + str(DoHutBaoHoa["DoHutBaoHoa"].values))
                        sum = sum + selected["AtLuongMua"].values[k]
                        next_nguy_co_chay_rung, khi_tuong_tong_hop = fixCalculateRisk(khi_tuong_ngay_hom_truoc,sum)
                    df.loc[df['Id'] == next_ids[k], 'NguyCo'] = next_nguy_co_chay_rung
                    df.loc[df['Id'] == next_ids[k], 'P'] = khi_tuong_tong_hop
                    df.loc[df['Id'] == next_ids[k], 'pHomTruoc'] = khi_tuong_ngay_hom_truoc
                    # print(next_nguy_co_chay_rung + " P= " + str(khi_tuong_tong_hop) + "at " + str(getDateValues[j])[:10])

            #firstTimeRun
            if(len(selected_first_time["LuongMua"].values) > 0 ):
                for k in range(len(selected_first_time["LuongMua"].values)):
                    if(special_time.empty):
                        pass
                    else:
                        try:
                            sum = sum + selected_first_time["AtLuongMua"].values[k]
                            # fix Must have equal len keys and value when setting with an iterable
                            if (float(special_time["NhietDo"].values) > 44.9):
                                special_time["NhietDo"].values = 44.9
                            DoHutBaoHoa = bang_tra_do_am.loc[
                                (abs(bang_tra_do_am['NhietDoKhongKhi'] - special_time["NhietDo"].values) == 0) & (
                                        abs(bang_tra_do_am['DoAmTuongDoi'] - special_time["DoAm"].values) == 0)]
                            nhietDoAt13 = special_time["NhietDo"].values
                            nguy_co_chay_rung,khi_tuong_tong_hop_default = calculateRisk(sum, khi_tuong_ngay_hom_truoc,nhietDoAt13,DoHutBaoHoa["DoHutBaoHoa"].values)
                            df.loc[df['Id'] == ids[k], 'pHomTruoc'] = khi_tuong_ngay_hom_truoc
                        except:
                            nguy_co_chay_rung,khi_tuong_tong_hop_default = calculateRisk(sum, khi_tuong_ngay_hom_truoc,44.9,DoHutBaoHoa["DoHutBaoHoa"].values)

                    df.loc[df['Id'] == ids[k], 'NguyCo'] = nguy_co_chay_rung
                    df.loc[df['Id'] == ids[k], 'P'] = khi_tuong_tong_hop_default
                    # print("P= " + str(khi_tuong_tong_hop_default) + "at " + str(getDateValues[j])[:10])
                
            khi_tuong_ngay_hom_truoc = khi_tuong_tong_hop_default
            sumLuongMuaList.append(sum)
            sum = 0

        df.loc[ df["HuongGio"] >= 360, "HuongGio"] = 0
        # deleteRecord()
        for i in range(len(df)):
            row = df.iloc[i]
            
            # Kiểm tra dữ liệu tại mỗi dòng có đủ và không bị NaN
            if not pd.isna(row["P"]) and not pd.isna(row["NguyCo"]) and not pd.isna(row["NhietDo"]) and not pd.isna(row["DoAm"]):
                insertKhiTuong1h(
                    "tbChiTietKhiTuong1h",
                    [
                        int(row["Id"]),
                        round(float(row["NhietDo"]), 2),
                        round(float(row["DoAm"]), 2),
                        float(row["TocDoGio"]),
                        int(row["HuongGio"]),
                        round(float(row["AtLuongMua"]), 2),
                        row["ThoiGian"],
                        row["KHTram"],
                        int(row["MaTram"]),
                        round(float(row["P"]), 2),
                        row["NguyCo"]
                    ]
                )

        # for i in range(len(df)):
        #     insertKhiTuong1h("tbChiTietKhiTuong1h",[int(df["Id"].iloc[i]), round(float(df["NhietDo"].iloc[i]),2),round(float(df["DoAm"].iloc[i]), 2),
        #                                             float(df["TocDoGio"].iloc[i]), int(df["HuongGio"].iloc[i]), round(float(df["AtLuongMua"].iloc[i]),2), 
        #                                             df["ThoiGian"].iloc[i], df["KHTram"].iloc[i], int(df["MaTram"].iloc[i]), 
        #                                             round(float(df["P"].iloc[i]),2) ,df["NguyCo"].iloc[i]])

    except Exception as e:
        logger.error(e)

def insertData(table_name, parameters):
    """insert data for Fire detected"""
    try:
        conn = checkconection()
        if conn:
            SQL_QUERY = (
                f"INSERT INTO {table_name} ({column[0]},{column[1]},{column[2]},{column[3]},{column[4]},{column[5]},{column[6]},{column[7]},{column[8]},{column[9]},{column[10]},{column[11]},{column[12]},{column[13]},{column[14]},{column[15]},{column[16]},{column[17]},{column[18]},{column[19]})"
                f"VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)")
            cursor = conn.cursor()
            cursor.execute(SQL_QUERY, parameters)

            conn.commit()
        
            #conn.close()
            logger.info(f"Inserting data in tbDamChay successful!")
                # Do your DB logic
        else:
            logger.error("[CRITICAL] Could not establish DB connection. Skipping operation.")
        
    except Exception as e:
        logger.error(f"Fail insert tbDamChay: {e}")
        pass

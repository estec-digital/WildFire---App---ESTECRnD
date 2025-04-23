import threading
import time
import requests
from requests.auth import HTTPDigestAuth
import os
import cv2
import numpy as np
import pyodbc
import traceback
from datetime import datetime
from flask import Flask
from flask_cors import CORS
import xml.etree.ElementTree as ET
import logging
import multiprocessing
import sys, ctypes  

# connection = pyodbc.connect(
#             "Driver={ODBC Driver 17 for SQL Server};"
#             "Server=192.168.54.39\\WFDS;Database=WFDS;"
#             "Uid=administrator;Pwd=Pass@work1"
#         )

# try:
#     cursor = connection.cursor()
#     # cursor.executemany(
#     #     "INSERT INTO tbAnhz (Image_name, Image_angle, Image_time, MaTram) VALUES (?, ?, ?, ?)",
        
#     # )
#     # connection.commit()
#     print("done insert")
#     #connection.close()

# except Exception as e:
#     #connection.close()
#     print ("something wrong", e)
#     # logger.error(f"[DB ERROR] {e}")
#     time.sleep(1)

# import pyodbc

# Set your SQL Server connection details
server = '192.168.54.39'
database = 'WFDS'
username = 'administrator'
password = 'Pass@work1'

# Connection string (adjust driver if needed)
connection_string = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password}"
)

# Your SQL query
query = """
SELECT TOP (1000) [Id],
       [NhietDo],
       [DoAm],
       [TocDoGio],
       [HuongGio],
       [LuongMua],
       [ThoiGian],
       [KHTram],
       [MaTram]
FROM [WFDS].[dbo].[tbChiTietKhiTuong]
ORDER BY [ThoiGian] DESC
"""

try:
    # Connect and execute
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        cursor.execute(query)

        # Fetch and display results
        rows = cursor.fetchall()
        for row in rows:
            print(row)

except Exception as e:
    print("❌ Error:", e)


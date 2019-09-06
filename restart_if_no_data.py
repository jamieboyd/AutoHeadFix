import pymysql
import datetime
from time import time
import os

db = pymysql.connect(host="142.103.107.236", user="slavePi", db="AHF_laser_cage", password="iamapoorslave")
query_sources = """SELECT* FROM `raw_data` WHERE `Cage` = %s
    ORDER BY `Timestamp` DESC LIMIT 1 """
cur = db.cursor()
cur.execute(query_sources, ["cage1",])

_, _, _, _, timestamp, _, _ = cur.fetchall()[0]

if time() - timestamp.timestamp() > 3600 :
    os.system("sudo reboot")

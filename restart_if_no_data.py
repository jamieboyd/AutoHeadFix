import pymysql
import datetime
from time import time
import os

cageID = ""
user = ""
pwd = ""
db = ""
with open("config.txt", "r") as file:
    configs = file.readlines()
    for config in configs:
        config = config.split("=")
        if config[0] == "cageID":
            cageID = config[1].rstrip("\n")
        if config[0] == "user":
            user = config[1].rstrip("\n")
        if config[0] == "pwd":
            pwd = config[1].rstrip("\n")
        if config[0] == "db":
            db = config[1].rstrip("\n")
db = pymysql.connect(host="142.103.107.236", user=user, db=db, password=pwd)
query_sources = """SELECT* FROM `raw_data` WHERE `Cage` = %s
    ORDER BY `Timestamp` DESC LIMIT 1 """
cur = db.cursor()
cur.execute(query_sources, [cageID, ])

_, _, _, _, timestamp, _, _ = cur.fetchall()[0]

if time() - timestamp.timestamp() > 3600 :
    os.system("sudo reboot")

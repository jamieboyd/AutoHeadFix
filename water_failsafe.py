##############################################################################
############ This program is used by AHF to monitor the water valve. #########
############ If at any point, the water valve malfunctions and stays #########
############  open for more then 5 seconds the pi will reboot and    #########
############  restart autoheadfix                                    #########
##############################################################################
##############################################################################


import RPi.GPIO as GPIO
import pymysql
from ast import literal_eval
from time import sleep, time
import os
GPIO.setmode(GPIO.BCM)
cageID = ""
user = ""
pwd = ""
db = ""
with open("/home/pi/config.txt", "r") as file:
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
db = pymysql.connect(host="localhost", user=user, db=db, password=pwd)
query_sources = """SELECT* FROM `configs` WHERE `Cage` = %s AND `Tag` = %s AND
`Dictionary_source` = "RewarderDict" ORDER BY `Timestamp` DESC LIMIT 1 """
cur = db.cursor()
cur.execute(query_sources, [cageID, "changed_hardware"])
#print(cur.fetchall()[0])
mouse, source, dictio, _, _ ,_  = cur.fetchall()[0]
data = {str(source): literal_eval("{}".format(dictio))}
print(data)
water_pin = data["changed_hardware"]["rewardPin"]
GPIO.setup(water_pin, GPIO.OUT)
water_on_time = 0.0
startTime = time()
while True:
    if time() > startTime + 300:
        break
    if GPIO.input(water_pin):
        water_on_time += 0.05
        sleep(0.05)
        if water_on_time >= 5:
            GPIO.setup(water_pin, GPIO.OUT)
            GPIO.output(water_pin, GPIO.LOW)
            #send text
            os.system("sudo reboot")
            pass
    else:
        sleep(3)

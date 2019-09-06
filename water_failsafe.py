import RPi.GPIO as GPIO
import pymysql
from ast import literal_eval
from time import sleep, time
import os
GPIO.setmode(GPIO.BCM)
db = pymysql.connect(host="localhost", user="pi", db="raw_data", password="AutoHead2015")
query_sources = """SELECT* FROM `configs` WHERE `Cage` = %s AND `Tag` = %s AND
`Dictionary_source` = "RewarderDict" ORDER BY `Timestamp` DESC LIMIT 1 """
cur = db.cursor()
cur.execute(query_sources, ["cage1", "changed_hardware"])
mouse, source, dictio = cur.fetchall()[0]
data = {str(source): literal_eval("{}".format(dictio))}
water_pin = data["rewardPin"]
water_on_time = 0.0
startTime = time()
while True:
    if time() > startTime + 300:
        break
    if GPIO.input(water_pin):
        water_on_time += 0.05
        sleep(0.05)
        if water_on_time >= 5:
            GPIO.setmode(GPIO.OUT, water_pin)
            GPIO.output(water_pin, GPIO.LOW)
            #send text
            os.system("sudo reboot")
            pass
    else:
        sleep(3)

import pymysql
import time
import getpass
from ast import literal_eval
tags = [2018121341, 2018121208, 2018121273, 2018121358]
jsonDict = {}
password = getpass.getpass(prompt= "Please enter the password for the database")
db = pymysql.connect(host="142.103.107.236", user="slavePi", db="AHF_laser_cage", password=password)
query_sources = """SELECT DISTINCT `Dictionary_source` FROM `configs` WHERE `Cage` = %s AND `Tag` = %s"""
cur = db.cursor()
cur.execute(query_sources, ["cage1", "changed_hardware"])

sources_list = [i[0] for i in cur.fetchall()]
query_config = """SELECT `Tag`,`Dictionary_source`,`Config` FROM `configs` WHERE `Tag` = %s
                                AND `Dictionary_source` = %s ORDER BY `Timestamp` DESC LIMIT 1"""
for sources in sources_list:
    cur.execute(query_config, ["changed_hardware", str(sources)])
    mouse, source, dictio = cur.fetchall()[0]
    if "Class" in str(source):
        data = {str(source): str(dictio)}
    else:
        data = {str(source): literal_eval("{}".format(dictio))}
    jsonDict.update(data)

miceDicts = {}
x = 0
for tag in tags:
    tempDict = {}
    cur.execute(query_sources, ["cage1", tag])

    sources_list = [i[0] for i in cur.fetchall()]
    for sources in sources_list:
        cur.execute(query_config, [tag, str(sources)])
        mouse, source, dictio = cur.fetchall()[0]
        if "Class" in str(source):
            data = {str(source): str(dictio)}
        else:
            data = {str(source): literal_eval("{}".format(dictio))}
        tempDict.update(data)
    miceDicts.update({tag: tempDict})

query_trial = """SELECT * FROM raw_data WHERE `Timestamp` >= %s AND `Tag` =  %s
    AND `Event` = 'lever_pull'"""
query_entry = """SELECT * FROM raw_data WHERE `Timestamp` >= %s AND `Tag` =  %s
    AND `Event` = 'entry'"""
query_licks = """SELECT * FROM raw_data WHERE `Timestamp` >= %s AND `Tag` =  %s
    AND `Event` = 'lick'"""
query_reward = """SELECT * FROM raw_data WHERE `Timestamp` >= %s AND `Tag` =  %s
    AND `Event` = 'reward'"""
day = time.localtime(time.time())
day = str(day[0]) + "-" + str(day[1]) + "-" + str(day[2])
yesterday = time.localtime(time.time() - 60*60*24)
yesterday = str(yesterday[0]) + "-" + str(yesterday[1]) + "-" + str(yesterday[2]) + "-12:00:00"
with open("QuickStats/" + day + ".txt", "w+") as f:
    f.write("Quick Stats for " + yesterday + " to " + day + "-12:00:00\n")
    for tag in tags:
        cur.execute(query_trial, [yesterday, tag])
        num_success = 0
        num_trials = 0
        for line in cur.fetchall():
            dict = literal_eval("{}".format(line[3]))
            print(line[1], line[2], line[3], line[6], line[0])
            num_trials += 1
            if int(dict['outcome']) > 0:
                num_success += 1
        cur.execute(query_entry, [yesterday, tag])
        num_entries = len(cur.fetchall())
        cur.execute(query_licks, [yesterday, tag])
        num_licks = len(cur.fetchall())
        cur.execute(query_reward, [yesterday, tag])
        num_rewards = len(cur.fetchall())
        f.write(str(tag) + "\n")
        f.write("Number of trials: " + str(num_trials) + "\n")
        f.write("Number of successful trials: " + str(num_success) + "\n")
        f.write("Number of entries: " + str(num_entries) + "\n")
        f.write("Number of licks: " + str(num_licks) + "\n")
        f.write("Number of rewards: " + str(num_rewards) + "\n")
    for key, value in jsonDict.items():
        f.write(str(key) + ": " + str(value) + "\n")
    for key, value in miceDicts.items():
        f.write(str(key) + ": \n")
        for k, v in value.items():
            f.write("    " + str(k) + ": " + str(v) + "\n")

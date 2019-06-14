#! /usr/bin/python
# -*-coding: utf-8 -*-
from time import time
from datetime import datetime
import pymysql
from ast import literal_eval
from AHF_Task import Task
import AHF_ClassAndDictUtils as CAD
from AHF_DataLogger import AHF_DataLogger
import json
import os
import pwd
import grp

class AHF_DataLogger_mysql(AHF_DataLogger):
    """
    Simple text-based data logger modified from the original Auto Head Fix code
    makes a new text logfile for each day, saved in default data path.

    Mouse data is stored in a specified folder, also as text files, one text file per mouse
    containing JSON formatted configuration and performance data. These files will opened and
    updated after each exit from the experimental tube, in case the program needs to be restarted
    The file name for each mouse contains RFID tag 0-padded to 13 spaces: AHF_mouse_1234567890123.jsn

    REQUESTED VALUES:
    "exit" for exits as event
    "lever_pull" as event for lever data
    "positions" as key for the lever positions in the event_dictionary of "lever_pull"

    """
    PSEUDO_MUTEX = 0
    """
    The class field PSEUDO_MUTEX helps prevent print statements from different places in the code (main vs
    callbacks) from executing at the same time, which leads to garbled output. Unlike a real mutex, execution
    of the thread is not halted while waiting on the PSEUDO_MUTEX, hence the loops with calls to sleep to
    allow the other threads of execution to continue while waiting for the mutex to be free. Also, read/write
    to the PSEUDO_MUTEX is not atomic; one thread may read PSEUDO_MUTEX as 0, and set it to 1, but in the
    interval between reading and writing to PSEUDO_MUTEX,another thread may have read PSEUDO_MUTEX as 0 and
    both threads think they have the mutex
    """
    defaultCage = 'cage1'
    defaultHost = "142.103.107.236"
    defaultUser = "slavePi"
    defaultDatabase = "AHF_laser_cage"
    defaultPassword = "iamapoorslave"

    localHost = 'localhost'
    localUser = 'pi'
    localDatabase = 'raw_data'
    localPassword = 'AutoHead2015'


    @staticmethod
    def about():
        return 'Data logger that prints mouse id, time, event type, and event dictionary to the shell and  to a mysql database.'

    @staticmethod
    def config_user_get(starterDict={}):
        # cage ID
        cageID = starterDict.get('cageID', AHF_DataLogger_mysql.defaultCage)
        response = input('Enter a name for the cage ID (currently {}): '.format(cageID))
        if response != '':
            cageID = response
        # mysql log
        # host
        DBhost = starterDict.get('DBhost', AHF_DataLogger_mysql.defaultHost)
        response = input('Enter a host for the database (currently {}): '.format(DBhost))
        if response != '':
            DBhost = response
        # user
        DBuser =starterDict.get('DBuser', AHF_DataLogger_mysql.defaultUser)
        response = input('Enter your user name for the database (currently {}): '.format(DBuser))
        if response != '':
            DBuser = response
        # database
        DB = starterDict.get('DB', AHF_DataLogger_mysql.defaultDatabase)
        response = input('Enter the database you want to connect to (currently {}): '.format(DB))
        if response != '':
            DB = response
        # password
        DBpwd = starterDict.get('DBpwd', AHF_DataLogger_mysql.defaultPassword)
        response = input('Enter your user password (currently {}): '.format(DBpwd))
        if response != '':
            DBpwd = response
        # update and return dict
        starterDict.update({'cageID': cageID, 'DBhost': DBhost, 'DBuser': DBuser,'DB': DB, 'DBpwd': DBpwd })

        return starterDict


    def saveToDatabase(self,query, values,remote):
        if remote == True:
            try:
                db1 = pymysql.connect(host=self.DBhost, user=self.DBuser, db=self.DB, password=self.DBpwd)
            except:
                print("Wasn't able to connect to remote database")
        else:
            db1 = pymysql.connect(host=self.localHost, user=self.localUser, db=self.localDatabase, password=self.localPassword)
        cur1 = db1.cursor()
        try:
            cur1.executemany(query, values)
            db1.commit()
        except pymysql.Error as e:
            try:
                print("MySQL Error [%d]: %s" % (e.args[0], e.args[1]))
                return None
            except IndexError:
                print("MySQL Error: %s" % str(e))
                return None
        except TypeError as e:
            print("MySQL Error: TypeError: %s" % str(e))
            return None
        except ValueError as e:
            print("MySQL Error: ValueError: %s" % str(e))
            return None
        db1.close()

    def getFromDatabase(self,query,values,remote):
        if remote == True:
            try:
                db2 = pymysql.connect(host=self.DBhost, user=self.DBuser, db=self.DB, password=self.DBpwd)
            except:
                print("Wasn't able to connect to remote database")
        else:
            db2 = pymysql.connect(host=self.localHost, user=self.localUser, db=self.localDatabase, password=self.localPassword)
        cur2 = db2.cursor()
        try:
            cur2.execute(query,values)
            rows = cur2.fetchall()
        except pymysql.Error as e:
            try:
                print("MySQL Error [%d]: %s" % (e.args[0], e.args[1]))
                return None
            except IndexError:
                print("MySQL Error: %s" % str(e))
                return None
        except TypeError as e:
            print("MySQL Error: TypeError: %s" % str(e))
            return None
        except ValueError as e:
            print("MySQL Error: ValueError: %s" % str(e))
            return None
        db2.close()
        return rows


    def makeLogFile (self):
        """
        Initiating database creation
        """
        print("setting up")
        raw_data_table_generation = """CREATE TABLE IF NOT EXISTS `raw_data` (`ID` int(11) NOT NULL AUTO_INCREMENT,`Tag` varchar(18) NOT NULL,`Event` varchar(50) NOT NULL,
                                    `Event_dict` varchar(2000) DEFAULT NULL,`Timestamp` timestamp(2) NULL DEFAULT NULL,`Cage` varchar(20) NOT NULL,
                                     `positions` blob, PRIMARY KEY (`ID`), UNIQUE KEY `Tag` (`Tag`,`Event`,`Timestamp`,`Cage`))
                                      ENGINE=InnoDB DEFAULT CHARSET=latin1"""

        config_data_table_generation = """CREATE TABLE IF NOT EXISTS `configs` (`ID` int(11) NOT NULL AUTO_INCREMENT,`Tag` varchar(18) NOT NULL,
                                        `Config` varchar(2000) NOT NULL,`Timestamp` timestamp(2) NULL DEFAULT NULL,`Cage` varchar(20) NOT NULL,
                                        `Dictionary_source` varchar(50) NOT NULL,
                                        PRIMARY KEY (`ID`),UNIQUE KEY `Tag` (`Tag`,`Timestamp`,`Cage`,`Dictionary_source`))
                                         ENGINE=InnoDB DEFAULT CHARSET=latin1"""
        hardwaretest_table_generation = """CREATE TABLE IF NOT EXISTS `hardwaretest` (`ID` int(11) NOT NULL AUTO_INCREMENT,
                                        `Timestamp` timestamp(2) NULL DEFAULT NULL,PRIMARY KEY (`ID`)) ENGINE=InnoDB DEFAULT CHARSET=latin1"""
        mice_table_generation = """CREATE TABLE IF NOT EXISTS `mice` (`ID` int(11) NOT NULL AUTO_INCREMENT,
                                    `Timestamp` timestamp(2) NULL DEFAULT NULL,`Cage` varchar(20) NOT NULL,`Tag` varchar(18) NOT NULL,`Note` varchar(100) NULL DEFAULT NULL,
                                    PRIMARY KEY (`ID`),UNIQUE KEY `Tag` (`Tag`,`Cage`)) ENGINE=InnoDB DEFAULT CHARSET=latin1"""
        try:
            self.saveToDatabase(raw_data_table_generation, [[]], True) # create table on remote DB
            self.saveToDatabase(raw_data_table_generation, [[]], False) # create table on local DB
            self.saveToDatabase(config_data_table_generation, [[]], False) # create config data table locally,
            self.saveToDatabase(config_data_table_generation, [[]], True) # create config data table remote
            self.saveToDatabase(hardwaretest_table_generation, [[]], True) # create hardware test table in remote DB
            self.saveToDatabase(hardwaretest_table_generation, [[]], False)  # create hardware test table in local DB
            self.saveToDatabase(mice_table_generation, [[]], False)  # create hardware test table in local DB
        except Exception as e:
                print("Tables could not be created. Error: ", str(e))


    def setup(self):
        self.cageID = self.settingsDict.get('cageID')
        self.DBhost = self.settingsDict.get('DBhost')
        self.DBuser = self.settingsDict.get('DBuser')
        self.DB = self.settingsDict.get('DB')
        self.DBpwd = self.settingsDict.get('DBpwd')
        self.makeLogFile()
        self.raw_save_query = """INSERT INTO `raw_data`(`Tag`,`Event`,`Event_dict`,`Timestamp`,`Cage`,`positions`)
        VALUES(%s,%s,%s,FROM_UNIXTIME(%s),%s,%s)"""
        self.config_save_query = """INSERT INTO `configs` (`Tag`,`Config`,`Timestamp`,`Cage`,`Dictionary_source`) VALUES(%s,%s,FROM_UNIXTIME(%s),%s,%s)"""
        self.add_mouse_query = """INSERT INTO `mice` (`Timestamp`,`Cage`,`Tag`,`Note`) VALUES(FROM_UNIXTIME(%s),%s,%s,%s)"""
        self.events = []
        self.water_available = False
        showDict = self.task.Show_testable_objects()

        self.events.append([0, 'SeshStart', None, time(),self.cageID,None])
        self.saveToDatabase(self.raw_save_query, self.events, False)
        self.saveToDatabase(self.raw_save_query, self.events, True)
        self.events = []

    def setdown(self):
        """
        Writes session end and closes log file
        """
        self.events.append([0, 'SeshEnd', None, time(),self.cageID,None])
        self.saveToDatabase(self.raw_save_query,self.events, False)
        self.saveToDatabase(self.raw_save_query, self.events, True)
        self.events = []

#####################################################################################
    def configGenerator(self,settings):
        """
        Each configuration file has config data for a single subject. This function loads data
        from all of them in turn, and returning each as a a tuple of (tagID, dictionary)
        """
        # get the mice first, therefore we need them in the `mice` table, at least their tag number and their cage
        # we will call the mice by their cage which is a class variable
        query_sources = """SELECT DISTINCT `Dictionary_source` FROM `configs` WHERE `Cage` = %s"""
        sources_list = [i[0] for i in list(self.getFromDatabase(query_sources, [str(self.cageID)], False))]
        query_config = """SELECT `Tag`,`Dictionary_source`,`Config` FROM `configs` WHERE `Tag` = %s
                                            AND `Dictionary_source` = %s ORDER BY `Timestamp` DESC LIMIT 1"""
        if settings == "current_subjects":
            mice_list = self.getMice()
            for mice in mice_list:
                s = {}
                for sources in sources_list:
                    try:
                        mouse, source, dictio = self.getFromDatabase(query_config, [str(mice), str(sources)], False)[0]
                    except:
                        mouse, source, dictio = self.getFromDatabase(query_config, ["default_subjects", str(sources)], False)[0]
                        mouse = mice
                    s.update({str(source): literal_eval("{}".format(dictio))})
                data = {int(mouse): s}
                yield(data)
        if settings == "default_subjects":
            for sources in sources_list:
                mouse, source, dictio = self.getFromDatabase(query_config, ["default_subjects", str(sources)], False)[0]
                data = {str(source): literal_eval("{}".format(dictio))}
                yield (data)
        if settings == "default_hardware":
            for sources in sources_list:
                mouse, source, dictio = self.getFromDatabase(query_config, ["default_hardware", str(sources)], False)[0]
                data = {str(source): literal_eval("{}".format(dictio))}
                yield (data)
        if settings == "changed_hardware":
            for sources in sources_list:
                mouse, source, dictio = self.getFromDatabase(query_config, ["changed_hardware", str(sources)], False)[0]
                data = {str(source): literal_eval("{}".format(dictio))}
                yield (data)

    def getMice(self):
        query_mice = """SELECT `Tag` FROM `mice` WHERE `Cage` = %s"""
        mice_list = [i[0] for i in list(self.getFromDatabase(query_mice, [str(self.cageID)], False))]
        return mice_list

    def getConfigData(self, tag,source):
        configs_get = """SELECT `Config` FROM `configs` WHERE `Tag` = %s AND `Dictionary_source` = %s  ORDER BY `Timestamp` DESC LIMIT 1"""
        values=[str(tag),str(source)]
        config_data = self.getFromDatabase(configs_get,values,False)[0][0]
        config_data = literal_eval("{}".format(config_data))
        return config_data

    def storeConfig(self, tag, configDict,source):
        # store in raw data
        self.events.append([tag, "config_{}".format(source), str(configDict), time(), self.cageID,None])
        self.saveToDatabase(self.raw_save_query, self.events, False)
        self.saveToDatabase(self.raw_save_query, self.events, True)
        self.events = []
        # store in the config table
        self.saveToDatabase(self.config_save_query, [[tag, str(configDict), time(), self.cageID, str(source)]], False)
        self.saveToDatabase(self.config_save_query, [[tag, str(configDict), time(), self.cageID, str(source)]], True)

    def saveNewMouse(self,tag,note, dictionary = {}):
        # store new mouse `Timestamp`,`Cage`,`Tag`,`Note`
        self.events.append([tag, 'added_to_cage', str(dict([("Notes",note)])), time(), self.cageID, None])
        self.saveToDatabase(self.raw_save_query, self.events, False)
        self.saveToDatabase(self.raw_save_query, self.events, True)
        self.events = []
        self.saveToDatabase(self.add_mouse_query, [[time(), self.cageID, tag,str(note)]], False)
        self.saveToDatabase(self.add_mouse_query, [[time(), self.cageID, tag,str(note)]], True)

    def retireMouse(self,tag,reason):
        # update information about a mouse `Timestamp`,`Cage`,`Tag`,`Activity`
        self.events.append([tag, 'retired', str(dict([("reason", reason)])), time(), self.cageID, None])
        self.saveToDatabase(self.raw_save_query, self.events, False)
        self.saveToDatabase(self.raw_save_query, self.events, True)
        self.events = []
        delete_mouse_query = """DELETE FROM `mice` WHERE `Tag`=%s"""
        self.saveToDatabase(delete_mouse_query, [[tag]], False)
        self.saveToDatabase(delete_mouse_query, [[tag]], True)


#######################################################################################
    def newDay(self):
        self.events.append([0, 'NewDay', None, time(),self.cageID,None])
        self.saveToDatabase(self.raw_save_query, self.events, False)
        self.saveToDatabase(self.raw_save_query, self.events, True)
        self.events = []

    def readFromLogFile(self, index):
        eventQuery = """SELECT `Event` from `raw_data` WHERE 1 ORDER BY `raw_data`.`Timestamp` LIMIT %s-1, 1"""
        eventDictQuery = """SELECT `Event_dict` from `raw_data` WHERE 1 ORDER BY `raw_data`.`Timestamp` LIMIT %s-1, 1"""
        event = self.getFromDatabase(eventQuery, [index], False)
        eventDict = self.getFromDatabase(eventDictQuery, [index], False)
        return (event, eventDict)

    def writeToLogFile(self, tag, eventKind, eventDict, timeStamp, toShellOrFile=3):
        super().writeToLogFile(tag, eventKind, eventDict, timeStamp, toShellOrFile)
        if (toShellOrFile & self.TO_FILE) > 0:
            if eventKind == "lever_pull":
                lever_positions = eventDict.get("positions")
                del eventDict["positions"]
                self.events.append([tag, eventKind, str(eventDict), timeStamp, self.cageID, lever_positions])
            else:
                self.events.append([tag, eventKind, str(eventDict), timeStamp, self.cageID, None])
        if eventKind == "exit" and toShellOrFile & self.TO_FILE:
            self.saveToDatabase(self.raw_save_query, self.events, False)
            self.saveToDatabase(self.raw_save_query, self.events, True)
            self.events = []
        if (toShellOrFile & self.TO_SHELL) > 0:
            print('{:013}\t{:s}\t{:s}\t{:s}\t{:s}\n'.format (tag, eventKind, str(eventDict), datetime.fromtimestamp(int(timeStamp)).isoformat(' '), self.cageID))

    def pingServers(self):
        query_save = """INSERT INTO `hardwaretest`(`Timestamp`)
                                VALUES(FROM_UNIXTIME(%s))"""
        values = [[time()]]
        query_get = """SELECT `Timestamp` FROM `hardwaretest` WHERE 1 ORDER BY `hardwaretest`.`Timestamp` DESC LIMIT 1"""
        try:
            self.saveToDatabase(query_save, values, False)
            response = str(self.getFromDatabase(query_get, [], False)[0][0])
            print("last test entry local DB: ", response)
        except:
            print("no connection to localhost")
        try:
            self.saveToDatabase(query_save, values, True)
            response = str(self.getFromDatabase(query_get, [], True)[0][0])
            print("last test entry remote DB: ", response)
        except:
            print("no connection to remote host")

    def hardwareTest(self):
        while True:
            inputStr = '\n************** Mouse Configuration ********************\nEnter:\n'
            inputStr += 'C to Change Remote server settings and cageID\n'
            inputStr += 'T to Test database connections\n'
            inputStr += 'J to generate a Json file of hardware settings from database\n'
            event = input (inputStr)
            if event == 'c' or event == 'C':
                result = input('Enter cageID, currently {:}: '.format(self.cageID))
                if result != '':
                    self.storeConfig("settings",{"new_CageID": result},"Datalogger")
                    self.settingsDict.update({'cageID': result})
                result = input('Enter Database host IP address, currently {:}: '.format(self.DBhost))
                if result != '':
                    self.settingsDict.update({'DBhost': result})
                result = input('Enter Database user name (you should make sure that the user has edit rights in the DB), currently {:}: '.format(self.DBuser))
                if result != '':
                    self.settingsDict.update({'DBuser': result})
                result = input('Enter Database name, currently {:}: '.format(self.DB))
                if result != '':
                    self.settingsDict.update({'DB': result})
                result = input('Enter database password for your user, currently {:}: '.format(self.DBpwd))
                if result != '':
                    self.settingsDict.update({'DBpwd': result})
                self.setup()
            elif event == 'T' or event == 't': # send timestamps to servers and then request the last timestamp
                self.pingServers()
            elif event == 'j' or event == 'J':
                response = input('generate json file from Database.\n D for default settings,\n L for last settings,\n type nothing to abort')
                if response != '':
                    jsonDict = {}
                    if response[0] == 'D' or response[0] == 'd':
                        settings = "default_hardware"
                        for config in self.configGenerator(settings):
                            jsonDict.update(config)
                    elif response[0] == 'L' or response[0] == 'l':
                        settings = "changed_hardware"
                        for config in self.configGenerator(settings):
                            jsonDict.update(config)
                    if len(jsonDict) > 0:
                        nameStr = input('please enter the filename. your file will be automatically named: AHF_filename_hardware.json')
                        configFile = 'AHF_' + nameStr + '_hardware.json'
                        with open(configFile, 'w') as fp:
                            fp.write(json.dumps(jsonDict, separators=('\n', '='), sort_keys=True, skipkeys=True))
                            fp.close()
                            uid = pwd.getpwnam('pi').pw_uid
                            gid = grp.getgrnam('pi').gr_gid
                            os.chown(configFile, uid, gid)  # we may run as root for pi PWM, so we need to explicitly set ownership
    # TODO settingsdict????

    def __del__(self):
        self.events.append([0, 'SeshEnd', None, time(),self.cageID,None])
        self.saveToDatabase(self.raw_save_query, self.events, False)
        self.saveToDatabase(self.raw_save_query, self.events, True)
        self.events = []
        self.setdown()

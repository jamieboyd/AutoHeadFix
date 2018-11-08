from AHF_Task import Task
from AHF_Mouse import Mouse, Mice
from RFIDTagReader import TagReader
from time import sleep


if __name__ == "__main__":
    task = Task(None)

    print (task.mouseConfigPath)

    reader = TagReader(task.serialPort, doChecksum = True)
    while True: 
        try:
            reader.clearBuffer()

            tag = reader.readTag()
            
            print ("Read Tag: " + str(tag))

            mouse = Mouse(tag, 0, 0, 0, 0, cageSettings.mouseConfigPath)

        except KeyboardInterrupt:
            break

    print("All mice in config files I hope!")

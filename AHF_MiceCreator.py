from AHF_CageSet import AHF_CageSet
from AHF_Mouse import Mouse, Mice
from AHF_TagReader import AHF_TagReader
from time import sleep


if __name__ == "__main__":
    cageSettings = AHF_CageSet()

    print (cageSettings.mouseConfigPath)

    reader = AHF_TagReader(cageSettings.serialPort)
    while True: 
        try:
            reader.clearBuffer()

            tag = reader.readTag()
            
            print ("Read Tag: " + str(tag))

            mouse = Mouse(tag, 0, 0, 0, 0, cageSettings.mouseConfigPath)

        except KeyboardInterrupt:
            break

    print("All mice in config files I hope!")

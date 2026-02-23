#! /usr/bin/python
#
# (C) 2014 juewei@fabfolk.com, All rights reserved.
#
# Distribute under MIT License or ask.
#
# Authors: mose@fabfolk.com, juewei@fabfolk.com, fabian@blaese.de, tom@tchilov.de


import os
import re
import time

from datetime import datetime

import serial # type: ignore







class SiPlus:
    """ class for interfacing with a Gossen Metrawatt Secutest SI+ over serial """
    def __init__(self, port):
        self.s = serial.Serial(
            port=port,
            baudrate=9600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1,
            xonxoff=True)



    """ context manager for the serial port """
    def __enter__(self):
        return self



    """ context manager for the serial port """
    def __exit__(self, type, value, traceback):
        self.s.close()



    """ add checksum and line ending to message and send it to the serial line """
    def write(self, message):
        self.s.reset_output_buffer()
        self.s.reset_input_buffer()

        message += "\r"
        self.s.write(message.encode("utf-8"))
        self.s.flush()



    """ calculate checksum of a message """
    def checksum(self, message):
        raw_bytes = message.encode("iso-8859-1")
        qsum_dec = ord("$")
        for i in raw_bytes:
            qsum_dec += int(i)

        # SI+ seems to be sensitive about checksum in lower/upper case hex.
        # Electric Testing Center by Gossen sends upper case, so we'll do that as well.
        return "%02X" % (qsum_dec & 0xff)



    """ read all available bytes """
    def read(self):
        while True:
            r = self.s.read(max(1, min(2048, self.s.in_waiting)))

            if r == b"":
                raise TimeoutError

            if r == b"\x13": # ignore first byte of response to WER?
                continue

            return r.decode("iso-8859-1")



    """ read one line, remove CRLF and validate checksum.
    returns read line, False on checksum error, None on timeout """
    def readline(self, printProgressLenData=False, printRxSpeed=False):
        response = ""
        substring = 0
        lenData = printProgressLenData

        begin = lastSet = datetime.now()
        while True:
            d = self.read()

            if d:
                response += d

            if lenData and (f := re.search(r"\$..", response[substring:])):
                end = f.end()
                s = response[substring:substring+end]
                n = int(re.search(r"(\d{4})\$", s).group(1))
                throughput = 1 / (datetime.now() - lastSet).total_seconds()

                width = os.get_terminal_size()[0]
                progress = n / lenData
                nonProgressChars = 7 # 3 spaces left, 2 for the [], 2 spaces right -> 7
                cols = int((width - nonProgressChars) * progress)
                secondsSinceBegin = (datetime.now() - begin).total_seconds()
                eta = abs(secondsSinceBegin - (secondsSinceBegin * (1 / progress)))
                etaStr = f"ETA {eta:>3.0f} s"
                lenEtaStr = len(etaStr)

                if cols < (lenEtaStr + 9):
                    leftCols = "=" * cols
                    rightCols = (" " * (width - len(leftCols)))
                    rightCols = f" {etaStr} " + rightCols[lenEtaStr+10:]
                else:
                    leftCols = "=" * (cols)
                    leftCols = leftCols[:-lenEtaStr-5] + f" {etaStr} " + leftCols[-3:]
                    rightCols = (" " * (width - len(leftCols) - 7))

                progressBar = "[" + leftCols + rightCols + "]"

                # print newline and jump to 2nd col of previous line because I like the aesthetic
                print(f"\r   {progressBar}  \n\033[F\r ", end="", flush=True)

                lastSet = datetime.now()
                substring += end + 1 # ";" at the end of the line

            if "\r\n" in response:
                break

        if printProgressLenData:
            print()
            print()

        if printRxSpeed:
            kB = len(response) / 1024
            secondsSinceBegin = (datetime.now() - begin).total_seconds()
            rate = kB / secondsSinceBegin
            print(f"received {lenData} data ({kB:.1f} kB) in {secondsSinceBegin:.2f} seconds ({throughput:.1f}/s / {(rate):.1f} kB/s)")
            print()

        # remove CRLF, split into lines
        parts = re.sub("[\r\n]+", "", response)

        string = ""
        strings = []
        i = 0
        # TODO: modernise this with regex search
        while i < len(parts):
            if parts[i] == "$":
                checksum = parts[i+1] + parts[i+2]
                i += 4

                if checksum.upper() != self.checksum(string):
                    print("checksum error for string: " + string)
                    print("expected: " + self.checksum(string) + ", received: " + checksum.upper())
                    return False

                strings.append(string.replace("ê", "Ω").replace("æ", "µ"))
                string = ""
                continue

            string += parts[i]
            i += 1

        if len(strings) == 0:
            return ""

        if len(strings) == 1:
            return strings[0]

        return strings



    """ send a command and read response """
    def request(self, command, printProgressLenData=False, printRxSpeed=False):
        time.sleep(0.01) # any sufficiently advanced technology is indistinguishable from magic
        self.write(command)

        return self.readline(printProgressLenData=printProgressLenData, printRxSpeed=printRxSpeed)



    """ check if an SI+ responds """
    def checkConnection(self, printOnSuccess=False):
        try:
            self.read()

            print("SI+ is still busy, waiting for it to stop yapping... alternatively, try power cycling the S2 to reset its serial port.")
            while self.read():
                time.sleep(0.1)

        except TimeoutError:
            pass # timeout means the SI+ is (quiet and ready to receive commands) or (not connected)


        try:
            # IDN0=0$9C
            r = self.request("IDN!0")

        except TimeoutError:
            print()
            print("SI+ is not responding. is the mode switch on S2 set to Off? did you connect RS232 with a 1:1 cable to the SI+ (not S2!)?")
            print("try power cycling the S2 to reset its serial port and/or unplugging the serial adapter. good luck!")
            quit()

        if printOnSuccess:
            print(f"connection established.")
            print()



    def getIdentification(self):
        # IDN0=0;GMN;SECUTEST-PSI;M702F;AU;21. September 2011  14:21:09$11
        r = self.request("IDN?").split("=")[1].split(";")

        modelName = r[2]
        modelCode = r[3]

        return f"{modelName} (model code: {modelCode})"



    def getBaseDeviceIdentification(self):
        # IDN1=1;GMN;Secutest S2N+W A14 D21;M7010;xx xxxxxx xxxx;1A;XXXXXXXX;10;10;GMC V 9.1$xx
        r = self.request("IDN1?").split("=")[1].split(";")

        modelName = r[2]
        modelCode = r[3]
        serialNo = r[4]
        firmware = r[9]

        return f"{modelName} (model code: {modelCode}, S/N: {serialNo}, firmware: {firmware})"



    def getStorageInfo(self):
        # ESR0=;058%;0259$83
        r = self.request("ESR?").split("=")[1].split(";")

        percentUsed = int(r[1].replace("%", ""))
        lenData = int(r[2])

        return (percentUsed, lenData)



    def getFunctionTests(self):
        # $24;$24; ... $24;$24;0195.;--.--;00.84;0.000;00:00:04$6F;$24;$24; ... $24;$24;0003.;--.--;00.02;0.000;00:00:18$5E;$24;$24; ... $24;$24
        r = self.request("FKT?")

        # known strings:
        # 0195.;--.--;00.84;0.000;00:00:04
        # 0003.;--.--;00.02;0.000;00:00:18

        return list(filter(lambda x: x != "", r)) # only non-empty strings



    def receiveData(self, printProgressLenData=False):
        print(f"receiving data from SI+, this might take a minute. go grab yourself a mate...")
        print()
        d = self.request("WER?", printProgressLenData=printProgressLenData, printRxSpeed=True)

        timestamp = datetime.strftime(datetime.now(), r"%Y-%m-%d_%H-%M-%S")
        filename = timestamp + "_siplus.csv"
        with open(filename, "x") as f:
            f.write("Name;BBCCDDEEFFGGHHIIKKLLMMNNOOPPQQRRSSTTUUVV;ID_Nr;ID-String2;Datum;Zeit;MW-R-SL;GW-R-SL;MW-DR-SL;GW-DR-SL; MW_R_ISO;GW_R_ISO; MW_U_ISO; GW_U_ISO;MW_DI_STR;GW_DI_STR;MW_UAC;GW_UAC;MW_UAC;GW_UAC;MW_EGA;GW_EGA;MW_EPA;GW_EPA;MW_EA;GW_EA;MW_EA_SFC;GW_EA_SFC;MW_GA;GW_GA;MW_PA_DC;GW_PA_DC;MW_PA_DC_SFC;GW_PA_DC_SFC\n")
            for d_ in d:
                f.write(d_ + "\n")

        print(f"saved data to {filename}.")







if __name__ == "__main__":
    try:
        with SiPlus("/dev/ttyUSB0") as siplus:
            print(f"trying to connect on {siplus.s.port}...")
            siplus.checkConnection(printOnSuccess=True)

            lenData = siplus.getStorageInfo()[1]
            siplus.receiveData(printProgressLenData=lenData)

            print("goodbye.")

    except KeyboardInterrupt:
        print()
        print("goodbye!")

#! /usr/bin/python
#
# (C) 2014 juewei@fabfolk.com, All rights reserved.
#
# Distribute under MIT License or ask.
#
# Authors: mose@fabfolk.com, juewei@fabfolk.com, fabian@blaese.de


import re,sys,string,serial,time


class M701x:
  """ Class for interfacing with Gossen Metrawatt devices over serial """
  def __init__(self, serial_port):
    self.port = serial_port
    self.__serial = serial.Serial(
                    port=self.port,
                    baudrate=9600,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=3,
                    xonxoff=True
                  )
    # r =  self.request('IDN!0')
    #

  def _read(self):
    """ reads one line, removes CRLF and validates checksum. Returns read line or False on checksum error """
    resp = self.__serial.readline().decode("iso-8859-1")

    # Remove CRLF, split into lines
    parts = re.sub('[\r\n]+', '', resp)

    string = ""
    strings = []
    i = 0
    while i < len(parts):
      if parts[i] == "$":
        chksum = parts[i+1] + parts[i+2]
        i += 4

        if chksum.lower() != self._checksum(string):
          print("Checksum error: " + string)
          print("check: " + chksum.lower() + ", calculated: " + self._checksum(string))
          return False

        string = re.sub('ê', 'Ω', string)
        string = re.sub('æ', 'µ', string)
        strings.append(string)
        string = ""
        continue

      string += parts[i]
      i += 1

    if len(strings) == 0:
      return ""
    if len(strings) == 1:
      return strings[0]
    return strings


  def _write(self,str):
    """ adds $-delimiter, checksum and line ending to str and sends it to the serial line """
    send = str + '$' + self._checksum(str) + '\r\n'
    self.__serial.write(send.encode('utf-8'))


  def _checksum(self,str):
    """ calculates checksum of a request/answer """
    raw_bytes = str.encode("iso-8859-1")
    qsum_dec = ord('$')
    for i in raw_bytes:
      qsum_dec += int(i)
    return "%02x" % (qsum_dec & 0xff)


  def _flush(self):
    """ discards all waiting answers in the buffer """
    self.__serial.flushInput()


  def request(self,command,retries=3):
    """ sends a command to device and parses reply """
    i = 0
    while i < retries:

      time.sleep(1) # M701x has a rate limit of 1 call per second?!

      self._flush()
      self._write(command)
      answer = self._read()
      # on checksum error retry
      # Answer .N<ADRESSE>=101 stands for checksum error
      if ((answer == False) or (answer[:2] == '.N' and answer[3:7] == '=101')):
        i+=1
        continue
      # on NACK return False and full answer
      elif (answer[:2] == '.N'):
        return False,answer
      # on ACK return True and address of device
      elif (answer[:2] == '.Y'):
        return True,answer[2:3]
      # on 'string answer' or unhandled answer return None and full answer
      else:
        return None,answer
    # if not sucessful within retries return False
    else:
      return False,'CHKSUM_ERROR'


  def sync_clock(self,idn):
    # needs more testing and ability to sync all devices (e.g. PSI + S2N)
    """ synchronizes device clock with PC """
    return self.request('DAT'+idn+'!'+time.strftime("%d.%m.%y;%H:%M:%S"))

  def data_csv(self):
    data = self.request('WER?');
    print("Name;BBCCDDEEFFGGHHIIKKLLMMNNOOPPQQRRSSTTUUVV;ID_Nr;ID-String2;Datum;Zeit;MW-R-SL;GW-R-SL;MW-DR-SL;GW-DR-SL; MW_R_ISO;GW_R_ISO; MW_U_ISO; GW_U_ISO;MW_DI_STR;GW_DI_STR;MW_UAC;GW_UAC;MW_UAC;GW_UAC;MW_EGA;GW_EGA;MW_EPA;GW_EPA;MW_EA;GW_EA;MW_EA_SFC;GW_EA_SFC;MW_GA;GW_GA;MW_PA_DC;GW_PA_DC;MW_PA_DC_SFC;GW_PA_DC_SFC;")
    for x in data[1]:
      print(x)




if __name__ == "__main__":
  m701 = M701x("/dev/ttyUSB0")

  m701.data_csv()

  # str = "\x13DATIMx=20.09.14;18:33$18\r\n\x11"
  #         ^what             ^param        ^XOFF

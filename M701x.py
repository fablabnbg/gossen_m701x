#! /usr/bin/python
#
# (C) 2014 juewei@fabfolk.com, All rights reserved.
#
# Distribute under MIT License or ask.
#
# Authors: mose@fabfolk.com, juewei@fabfolk.com


import re,sys,string,serial,time


class M701x:
  """ Class for interfacing with Gossen Metrawatt devices over serial """
  def __init__(self, serial_port):
    self.port = serial_port
    self.serial = serial.Serial(
                    port=self.port,
                    baudrate=9600,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=3,
                    xonxoff=True
                  )

  def read(self):
    """ reads one line, removes CRLF and validates checksum. Returns read line or False on checksum error """
    (answer,checksum) = string.split(self.serial.readline(),'$')
    checksum = re.sub('[\r\n+]','',checksum).lower()
    if (checksum == self.checksum(answer)):
      return answer
    else:
      return False


  def write(self,str):
    """ adds $-delimiter, checksum and line ending to str and sends it to the serial line """
    self.serial.write(str + '$' + self.checksum(str) + '\r\n')

  def checksum(self,str):
    """ calculates checksum of a request/answer """
    qsum_dec = ord('$')
    for i in str:
      d = ord(i)
      qsum_dec += d
    return "%x" % (qsum_dec & 0xff)

  def flush(self):
    """ discards all waiting answers in the buffer """
    self.serial.flushInput()

  def request(self,command,retries=3):
    """ sends a command to device and parses reply """
    i = 0
    while i < retries:

      time.sleep(1) # M701x has a rate limit of 1 call per second?!

      self.flush()
      self.write(command)
      answer = self.read()
      # on checksum error retry
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





if __name__ == "__main__":
  m701 = M701x(sys.argv[1])
  #m701.write("IDN?")
  #print m701.read()
  print m701.request('IDN!0')
  print m701.request('IDN?')
  print m701.request('BEEP!')
  print m701.sync_clock('0');
  print m701.sync_clock('1');

  # str = "\x13DATIMx=20.09.14;18:33$18\r\n\x11"
  #         ^what             ^param        ^XOFF
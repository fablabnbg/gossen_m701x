#! /usr/bin/python
#
# (C) 2014 juewei@fabfolk.com, All rights reserved.
#
# Distribute under MIT License or ask.
#
# Authors: mose@fabfolk.com, juewei@fabfolk.com


import re,sys,string,serial


class M701x:
  """
  Class for interfacing with Gossen Metrawatt devices over serial
  """
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
    """reads one line, removes CRLF and validates checksum. Returns read line or False on checksum error"""
    (answer,checksum) = string.split(self.serial.readline(),'$')
    checksum = re.sub('[\r\n+]','',checksum).lower()
    if (checksum == self.checksum(answer)):
      return answer
    else:
      return False


  def write(self,str):
    """adds $-delimiter, checksum and line ending to str and sends it to the serial line"""
    self.serial.write(str + '$' + self.checksum(str) + '\r\n')

  def checksum(self,str):
    """calculates checksum of a request/answer"""
    qsum_dec = ord('$')
    for i in str:
      d = ord(i)
      qsum_dec += d
    return "%x" % (qsum_dec & 0xff)

  def flush(self):
    """discards all waiting answers in the buffer"""
    self.serial.flushInput()

if __name__ == "__main__":
  m701 = M701x(sys.argv[1])
  m701.write("IDN?")
  print m701.read()

  # str = "\x13DATIMx=20.09.14;18:33$18\r\n\x11"
  #         ^what             ^param        ^XOFF
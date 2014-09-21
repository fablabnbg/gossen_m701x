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
    """reads one line"""
    return self.serial.readline()

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

if __name__ == "__main__":
  m701 = M701x(sys.argv[1])
  m701.write("IDN?")
  str = m701.read()
  print str

  # str = "\x13DATIMx=20.09.14;18:33$18\r\n\x11"
  #         ^what             ^param        ^XOFF
  # str = re.sub("[\x13\x11\r\n]+", "", str)
  # (cmd,csum) = string.split(str, '$')
  # if (csum != checksum(cmd)):
  #   print "Checksum error '%s': %s != %s" % (str,csum,checksum(cmd))
  #   sys.exit(1)




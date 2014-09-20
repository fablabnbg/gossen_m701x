#! /usr/bin/python
#
# (C) 2014 jw@fabfolk.com, All rights reserved.
#
# Distribute under MIT License or ask.
# 
 
import re,sys,string,serial


class M701x:
  """
  Tolle Klasse
  """
  def __init__(self, serial_port):
    self.port = serial_port
    self.serial = serial.Serial(port=self.port, baudrate=9600, )

  def read(self):
    """reads until X_ON seen, (one low level protocol frame)"""
    self.serial.readline(eol='\x11')

  def write(self,str):
    """adds X_OFF, $, checksum, CR, X_ON to str, 
       and sends it to the serial line
    """
    self.serial.write('\x13' + str + '$' + checksum(str) + '\r\x11')

  def checksum(self,str):
    qsum_dec = ord('$')
    for i in str:
      d = ord(i)
      qsum_dec += d
    return "%x" % (qsum_dec & 0xff)

if __name__ == "__main__":
  m701 = M701x('/dev/ttyUSB0')
  m701.write("Hallo")
  str= m701.read()
  print str

  # str = "\x13DATIMx=20.09.14;18:33$18\r\n\x11"
  #         ^what             ^param        ^XOFF
  # str = re.sub("[\x13\x11\r\n]+", "", str)
  # (cmd,csum) = string.split(str, '$')
  # if (csum != checksum(cmd)):
  #   print "Checksum error '%s': %s != %s" % (str,csum,checksum(cmd))
  #   sys.exit(1)




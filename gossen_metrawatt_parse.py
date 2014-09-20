#! /usr/bin/python

import re,sys,string

str = "\x13DATIMx=20.09.14;18:33$18\r\n\x11"
#          ^what          ^param        ^XOFF

str = re.sub("[\x13\x11\r\n]+", "", str)
(cmd,csum) = string.split(str, '$')
if (csum != checksum(cmd)):
  print "Checksum error '%s': %s != %s" % (str,csum,checksum(cmd))
  sys.exit(1)


class M701x:
  def __init__(self, serial_port):
    self.port = serial_port
    self.serial = serial.Serial(port=self.port, baudrate=9600, )

  def read(self):
    self.serial.readline(eol='\x11')

  def write(self,str):
    self.serial.write('\x13' + str + '$' + checksum(str) + '\r\x11')

  def checksum(str):
    qsum_dec = ord('$')
    for i in str:
      d = ord(i)
      qsum_dec += d
    return "%x" % (qsum_dec & 0xff)


m701 = M701x('/dev/ttyUSB0')
m701.write("Hallo")
str= m701.read()
print str





import os
import logging
import sys
import time
import subprocess

from ctypes import *
from config import DUMMY_MONITOR

logger = logging.getLogger(__name__)

# Pin definition
RST_PIN  = 17
DC_PIN   = 25
CS_PIN   = 8
BUSY_PIN = 24
PWR_PIN  = 18
MOSI_PIN = 10
SCLK_PIN = 11

class RaspberryPi:
  def __init__(self):
    import spidev
    import gpiozero
    
    self.SPI = spidev.SpiDev()
    self.GPIO_RST_PIN  = gpiozero.LED(RST_PIN)
    self.GPIO_DC_PIN   = gpiozero.LED(DC_PIN)
    # self.GPIO_CS_PIN   = gpiozero.LED(CS_PIN)
    self.GPIO_PWR_PIN  = gpiozero.LED(PWR_PIN)
    self.GPIO_BUSY_PIN   = gpiozero.Button(BUSY_PIN, pull_up = False)

  def digital_write(self, pin, value):
    if pin == RST_PIN:
      if value:
        self.GPIO_RST_PIN.on()
      else:
        self.GPIO_RST_PIN.off()
    elif pin == DC_PIN:
      if value:
        self.GPIO_DC_PIN.on()
      else:
        self.GPIO_DC_PIN.off()
    # elif pin == CS_PIN:
    #   if value:
    #     self.GPIO_CS_PIN.on()
    #   else:
    #     self.GPIO_CS_PIN.off()
    elif pin == PWR_PIN:
      if value:
        self.GPIO_PWR_PIN.on()
      else:
        self.GPIO_PWR_PIN.off()

  def digital_read(self, pin):
    if pin == BUSY_PIN:
      return self.GPIO_BUSY_PIN.value
    elif pin == RST_PIN:
      return self.RST_PIN.value
    elif pin == DC_PIN:
      return self.DC_PIN.value
    # elif pin == CS_PIN:
    #   return self.CS_PIN.value
    elif pin == PWR_PIN:
      return self.PWR_PIN.value

  def delay_ms(self, delaytime):
    time.sleep(delaytime / 1000.0)

  def spi_writebyte(self, data):
    self.SPI.writebytes(data)

  def spi_writebyte2(self, data):
    self.SPI.writebytes2(data)

  def DEV_SPI_write(self, data):
    self.DEV_SPI.DEV_SPI_SendData(data)

  def DEV_SPI_nwrite(self, data):
    self.DEV_SPI.DEV_SPI_SendnData(data)

  def DEV_SPI_read(self):
    return self.DEV_SPI.DEV_SPI_ReadData()

  def module_init(self, cleanup=False):
    self.GPIO_PWR_PIN.on()
    
    if cleanup:
      find_dirs = [
        os.path.dirname(os.path.realpath(__file__)),
        '/usr/local/lib',
        '/usr/lib',
      ]
      self.DEV_SPI = None
      for find_dir in find_dirs:
        val = int(os.popen('getconf LONG_BIT').read())
        logging.debug("System is %d bit"%val)
        if val == 64:
          so_filename = os.path.join(find_dir, 'DEV_Config_64.so')
        else:
          so_filename = os.path.join(find_dir, 'DEV_Config_32.so')
        if os.path.exists(so_filename):
          self.DEV_SPI = CDLL(so_filename)
          break
      if self.DEV_SPI is None:
        RuntimeError('Cannot find DEV_Config.so')

      self.DEV_SPI.DEV_Module_Init()

    else:
      # SPI device, bus = 0, device = 0
      self.SPI.open(0, 0)
      self.SPI.max_speed_hz = 4000000
      self.SPI.mode = 0b00
    return 0

  def module_exit(self, cleanup=False):
    logger.debug("spi end")
    self.SPI.close()

    self.GPIO_RST_PIN.off()
    self.GPIO_DC_PIN.off()
    self.GPIO_PWR_PIN.off()
    logger.debug("close 5V, Module enters 0 power consumption ...")
    
    if cleanup:
      self.GPIO_RST_PIN.close()
      self.GPIO_DC_PIN.close()
      # self.GPIO_CS_PIN.close()
      self.GPIO_PWR_PIN.close()
      self.GPIO_BUSY_PIN.close()

class JetsonNano:
  def __init__(self):
    import ctypes
    find_dirs = [
      os.path.dirname(os.path.realpath(__file__)),
      '/usr/local/lib',
      '/usr/lib',
    ]
    self.SPI = None
    for find_dir in find_dirs:
      so_filename = os.path.join(find_dir, 'sysfs_software_spi.so')
      if os.path.exists(so_filename):
        self.SPI = ctypes.cdll.LoadLibrary(so_filename)
        break
    if self.SPI is None:
      raise RuntimeError('Cannot find sysfs_software_spi.so')

    import Jetson.GPIO
    self.GPIO = Jetson.GPIO

  def digital_write(self, pin, value):
    self.GPIO.output(pin, value)

  def digital_read(self, pin):
    return self.GPIO.input(BUSY_PIN)

  def delay_ms(self, delaytime):
    time.sleep(delaytime / 1000.0)

  def spi_writebyte(self, data):
    self.SPI.SYSFS_software_spi_transfer(data[0])

  def spi_writebyte2(self, data):
    for i in range(len(data)):
      self.SPI.SYSFS_software_spi_transfer(data[i])

  def module_init(self):
    self.GPIO.setmode(self.GPIO.BCM)
    self.GPIO.setwarnings(False)
    self.GPIO.setup(RST_PIN, self.GPIO.OUT)
    self.GPIO.setup(DC_PIN, self.GPIO.OUT)
    self.GPIO.setup(CS_PIN, self.GPIO.OUT)
    self.GPIO.setup(PWR_PIN, self.GPIO.OUT)
    self.GPIO.setup(BUSY_PIN, self.GPIO.IN)
    
    self.GPIO.output(PWR_PIN, 1)
    
    self.SPI.SYSFS_software_spi_begin()
    return 0

  def module_exit(self):
    logger.debug("spi end")
    self.SPI.SYSFS_software_spi_end()

    logger.debug("close 5V, Module enters 0 power consumption ...")
    self.GPIO.output(RST_PIN, 0)
    self.GPIO.output(DC_PIN, 0)
    self.GPIO.output(PWR_PIN, 0)

    self.GPIO.cleanup([RST_PIN, DC_PIN, CS_PIN, BUSY_PIN, PWR_PIN])


class SunriseX3:
  Flag   = 0

  def __init__(self):
    import spidev
    import Hobot.GPIO

    self.GPIO = Hobot.GPIO
    self.SPI = spidev.SpiDev()

  def digital_write(self, pin, value):
    self.GPIO.output(pin, value)

  def digital_read(self, pin):
    return self.GPIO.input(pin)

  def delay_ms(self, delaytime):
    time.sleep(delaytime / 1000.0)

  def spi_writebyte(self, data):
    self.SPI.writebytes(data)

  def spi_writebyte2(self, data):
    # for i in range(len(data)):
    #   self.SPI.writebytes([data[i]])
    self.SPI.xfer3(data)

  def module_init(self):
    if self.Flag == 0:
      self.Flag = 1
      self.GPIO.setmode(self.GPIO.BCM)
      self.GPIO.setwarnings(False)
      self.GPIO.setup(RST_PIN, self.GPIO.OUT)
      self.GPIO.setup(DC_PIN, self.GPIO.OUT)
      self.GPIO.setup(CS_PIN, self.GPIO.OUT)
      self.GPIO.setup(PWR_PIN, self.GPIO.OUT)
      self.GPIO.setup(BUSY_PIN, self.GPIO.IN)

      self.GPIO.output(PWR_PIN, 1)
    
      # SPI device, bus = 0, device = 0
      self.SPI.open(2, 0)
      self.SPI.max_speed_hz = 4000000
      self.SPI.mode = 0b00
      return 0
    else:
      return 0

  def module_exit(self):
    logger.debug("spi end")
    self.SPI.close()

    logger.debug("close 5V, Module enters 0 power consumption ...")
    self.Flag = 0
    self.GPIO.output(RST_PIN, 0)
    self.GPIO.output(DC_PIN, 0)
    self.GPIO.output(PWR_PIN, 0)

    self.GPIO.cleanup([RST_PIN, DC_PIN, CS_PIN, BUSY_PIN], PWR_PIN)

if not DUMMY_MONITOR:
  if sys.version_info[0] == 2:
    process = subprocess.Popen("cat /proc/cpuinfo | grep Raspberry", shell=True, stdout=subprocess.PIPE)
  else:
    process = subprocess.Popen("cat /proc/cpuinfo | grep Raspberry", shell=True, stdout=subprocess.PIPE, text=True)
  output, _ = process.communicate()
  if sys.version_info[0] == 2:
    output = output.decode(sys.stdout.encoding)

  if "Raspberry" in output:
    implementation = RaspberryPi()
  elif os.path.exists('/sys/bus/platform/drivers/gpio-x3'):
    implementation = SunriseX3()
  else:
    implementation = JetsonNano()

  for func in [x for x in dir(implementation) if not x.startswith('_')]:
    setattr(sys.modules[__name__], func, getattr(implementation, func))

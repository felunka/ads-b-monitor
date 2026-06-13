import logging
import epdconfig

import PIL
from PIL import Image
import io

# Display resolution
EPD_WIDTH     = 960
EPD_HEIGHT    = 640

logger = logging.getLogger(__name__)

class EPD:
  def __init__(self):
    self.reset_pin = epdconfig.RST_PIN
    self.dc_pin = epdconfig.DC_PIN
    self.busy_pin = epdconfig.BUSY_PIN
    self.cs_pin = epdconfig.CS_PIN
    self.width = EPD_WIDTH
    self.height = EPD_HEIGHT
    self.BLACK  = 0x000000   #   00  BGR
    self.WHITE  = 0xffffff   #   01
    self.YELLOW = 0x00ffff   #   10
    self.RED  = 0x0000ff   #   11

    
  # Hardware reset
  def reset(self):
    epdconfig.digital_write(self.reset_pin, 1)
    epdconfig.delay_ms(200) 
    epdconfig.digital_write(self.reset_pin, 0)     # module reset
    epdconfig.delay_ms(2)
    epdconfig.digital_write(self.reset_pin, 1)
    epdconfig.delay_ms(200)   

  def send_command(self, command):
    epdconfig.digital_write(self.dc_pin, 0)
    epdconfig.digital_write(self.cs_pin, 0)
    epdconfig.spi_writebyte([command])
    epdconfig.digital_write(self.cs_pin, 1)

  def send_data(self, data):
    epdconfig.digital_write(self.dc_pin, 1)
    epdconfig.digital_write(self.cs_pin, 0)
    epdconfig.spi_writebyte([data])
    epdconfig.digital_write(self.cs_pin, 1)

  # send a lot of data   
  def send_data2(self, data):
    epdconfig.digital_write(self.dc_pin, 1)
    epdconfig.digital_write(self.cs_pin, 0)
    epdconfig.spi_writebyte2(data)
    epdconfig.digital_write(self.cs_pin, 1)
    
  def ReadBusy(self):
    logger.debug("e-Paper busy H")
    epdconfig.delay_ms(100)
    while(epdconfig.digital_read(self.busy_pin) == 0):    # 0: idle, 1: busy
      epdconfig.delay_ms(5)
    logger.debug("e-Paper busy release")
    
  def TurnOnDisplay(self):
    self.send_command(0x12) # DISPLAY_REFRESH
    self.send_data(0X00)
    self.ReadBusy()
    
  def init(self):
    if (epdconfig.module_init() != 0):
      return -1
    # EPD hardware init start

    self.reset()
    self.ReadBusy()

    self.send_command(0x00)
    self.send_data(0x0F)	
    self.send_data(0x29)	

    self.send_command(0x06)
    self.send_data(0x0F)	
    self.send_data(0x8B)	
    self.send_data(0x93)	
    self.send_data(0xC1)  # A1

    
    self.send_command(0x41)
    self.send_data(0x00)	

    self.send_command(0x50)
    self.send_data(0x37)	

    self.send_command(0x60)
    self.send_data(0x02)	
    self.send_data(0x02)	

    self.send_command(0x61)	
    self.send_data(int(self.width/256))
    self.send_data(self.width%256)
    self.send_data(int(self.height/256))
    self.send_data(self.height%256)

    self.send_command(0x62)
    self.send_data(0x98) 
    self.send_data(0x98)
    self.send_data(0x98) 
    self.send_data(0x75)
    self.send_data(0xCA) 
    self.send_data(0xB2)	
    self.send_data(0x98) 
    self.send_data(0x7E) 

    self.send_command(0x65)
    self.send_data(0x00)	
    self.send_data(0x00)	
    self.send_data(0x00)	
    self.send_data(0x00)	
    
    self.send_command(0xE7)
    self.send_data(0x1C)	

    self.send_command(0xE3)
    self.send_data(0x00)	

    self.send_command(0xE9)	
    self.send_data(0x01)

    self.send_command(0x30)
    self.send_data(0x08) 		

    self.send_command(0x04)
    self.ReadBusy()
    return 0

  def getbuffer(self, image):
    # Create a pallette with the 4 colors supported by the panel
    pal_image = Image.new("P", (1,1))
    pal_image.putpalette( (0,0,0,  255,255,255,  255,255,0,   255,0,0) + (0,0,0)*252)

    # Check if we need to rotate the image
    imwidth, imheight = image.size
    if(imwidth == self.width and imheight == self.height):
      image_temp = image
    elif(imwidth == self.height and imheight == self.width):
      image_temp = image.rotate(90, expand=True)
    else:
      logger.warning("Invalid image dimensions: %d x %d, expected %d x %d" % (imwidth, imheight, self.width, self.height))

    # Convert the soruce image to the 4 colors, dithering if needed
    image_4color = image_temp.convert("RGB").quantize(palette=pal_image, dither=0)
    buf_4color = bytearray(image_4color.tobytes('raw'))

    # into a single byte to transfer to the panel
    if self.width % 4 == 0 :
      Width = self.width // 4
    else :
      Width = self.width // 4 + 1
    Height = self.height 
    buf = [0x00] * int(Width * Height)
    idx = 0
    for j in range(0, Height):
      for i in range(0, Width):
          buf[i + j * Width] = (buf_4color[idx] << 6) + (buf_4color[idx+1] << 4) + (buf_4color[idx+2] << 2) + buf_4color[idx+3]
          idx = idx + 4
    return buf

  def _send_u16_be(self, value):
    self.send_data((value >> 8) & 0xFF)
    self.send_data(value & 0xFF)

  def _prepare_bw_patch(self, image, x, y):
    # UC8179 partial window addressing is aligned to 8 horizontal pixels.
    if image.mode != "1":
      image = image.convert("1")

    if x < 0:
      image = image.crop((-x, 0, image.width, image.height))
      x = 0
    if y < 0:
      image = image.crop((0, -y, image.width, image.height))
      y = 0

    if x >= self.width or y >= self.height:
      return None

    if x + image.width > self.width:
      image = image.crop((0, 0, self.width - x, image.height))
    if y + image.height > self.height:
      image = image.crop((0, 0, image.width, self.height - y))

    if image.width == 0 or image.height == 0:
      return None

    x_aligned = x // 8 * 8
    dropped_left = x - x_aligned
    if dropped_left:
      image = image.crop((dropped_left, 0, image.width, image.height))
      x = x_aligned

    width_aligned = image.width // 8 * 8
    if width_aligned == 0:
      return None
    if width_aligned != image.width:
      image = image.crop((0, 0, width_aligned, image.height))

    return image, x, y

  def partial_bw_test(self, image, x, y, write_red_plane=False):
    """
    Experimental UC8179-style partial update test for B/W patches.

    This does not change the normal full-refresh path. It should be called
    only after init() and before sleep().
    """
    prepared = self._prepare_bw_patch(image, x, y)
    if prepared is None:
      logger.warning("Skipping partial BW test: empty or out-of-range window")
      return False

    image_bw, x, y = prepared
    width, height = image_bw.size
    x_end = x + width - 1
    y_end = y + height - 1

    # Empirical values used by many UC8179 partial flows.
    self.send_command(0x50)
    self.send_data(0xA9)
    self.send_data(0x07)

    self.send_command(0x91)  # PTIN
    self.send_command(0x90)  # PTL
    self.send_data((x >> 8) & 0x03)
    self.send_data(x & 0xF8)
    self.send_data((x_end >> 8) & 0x03)
    self.send_data((x_end & 0xF8) | 0x07)
    self._send_u16_be(y)
    self._send_u16_be(y_end)
    self.send_data(0x01)

    # DTM1 payload for this patch only (1-bit per pixel, horizontal packing).
    self.send_command(0x10)
    self.send_data2(list(image_bw.tobytes()))

    # Optional DTM2 write for experiments where the red plane must be explicit.
    if write_red_plane:
      self.send_command(0x13)
      self.send_data2([0x00] * (width * height // 8))

    self.TurnOnDisplay()
    self.send_command(0x92)  # PTOUT
    return True

  def display(self, image):
    self.send_command(0x10)
    self.send_data2(image)
          
    self.TurnOnDisplay()
    
  def Clear(self, color=0x55):
    if self.width % 4 == 0 :
      Width = self.width // 4
    else :
      Width = self.width // 4 + 1
    Height = self.height

    self.send_command(0x10)
    for j in range(0, Height):
      for i in range(0, Width):
          self.send_data(color)
    self.TurnOnDisplay()

  def sleep(self):
    self.send_command(0x02) # POWER_OFF
    self.send_data(0X00)
    epdconfig.delay_ms(100)
    
    self.send_command(0x07) # DEEP_SLEEP
    self.send_data(0XA5)
    
    epdconfig.delay_ms(2000)
    epdconfig.module_exit()

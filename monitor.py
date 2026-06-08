import PIL
import time
import textwrap
from PIL import Image,ImageDraw,ImageFont
from display_lib import EPD

from config import DUMMY_MONITOR

class Monitor:

  def __init__(self):
    self.epd = EPD()
    if not DUMMY_MONITOR:
      self.image = Image.new('RGB', (self.epd.width, self.epd.height), self.epd.WHITE)
      self.show_now()

    self.font15 = ImageFont.truetype("data/OpenSans.ttf", 15)
    self.font18 = ImageFont.truetype("data/OpenSans.ttf", 18)
    self.font24 = ImageFont.truetype("data/OpenSans.ttf", 24)
    self.font30 = ImageFont.truetype("data/OpenSans.ttf", 30)


  def clear(self):
    self.image = Image.new('RGB', (self.epd.width, self.epd.height), self.epd.WHITE)  # 255: clear the frame
    self.show_now()
    time.sleep(3)
    
  
  def render_planes(self, planes):
    if len(planes) > 5:
      return
    
    plane_icon = Image.open("data/plane.png", "r").resize((32, 32))
    direction_icon = Image.open("data/direction.png", "r")
    
    rotated_image = Image.new('RGB', (self.epd.height, self.epd.width), self.epd.WHITE)
    draw = ImageDraw.Draw(rotated_image)
    
    for index, plane in enumerate(planes):
      offset_top = 192 * index
      
      # Render plane basic data
      draw.text((220, offset_top), f"{plane.callsign} ({plane.route.get_route().get('flight_no', '-')})", font=self.font24, fill=self.epd.BLACK)
      if plane.owner != "":
        draw.text((220, offset_top + 25), plane.owner, font=self.font15, fill=self.epd.BLACK)
      elif plane.operator_callsign != "":
        draw.text((220, offset_top + 25), plane.operator_callsign, font=self.font15, fill=self.epd.BLACK)
      draw.line((0, offset_top+48, 430, offset_top+48), fill=self.epd.RED)
      draw.text((220, offset_top + 50), f"Model: {plane.model}", font=self.font15, fill=self.epd.BLACK)
      draw.text((220, offset_top + 70), f"Land: {plane.country}", font=self.font15, fill=self.epd.BLACK)

      # Render approach/departure path
      plane_path = plane.route.get_path()
      if "arrival" in plane_path:
        path_text = ""
        if plane_path["arrival"]:
          path_text = f"APR {plane_path['runway']}"
        else:
          path_text = f"DEP {plane_path['runway']}"
        draw.text((460, offset_top), path_text, font=self.font24, fill=self.epd.BLACK)

      # Observation reference indicator
      observation_reference = plane.distance_and_direction_to_observer()
      draw.text((580, offset_top + 32), f"{round(observation_reference[0])}m", font=self.font15, fill=self.epd.BLACK)
      rotated_direction_icon = direction_icon.rotate(observation_reference[1], expand=True)
      rotated_image.paste(rotated_direction_icon, (590, offset_top + 5), rotated_direction_icon)

      # Render route
      draw.text((230, offset_top + 110), plane.route.get_route().get('from_iata', '-'), font=self.font30, fill=self.epd.BLACK)
      rotated_image.paste(plane_icon, (310, offset_top + 115), plane_icon)
      draw.text((360, offset_top + 110), plane.route.get_route().get('to_iata', '-'), font=self.font30, fill=self.epd.BLACK)

      from_airport = "\n".join(textwrap.wrap(plane.route.get_route().get('from', '-'), width=12))
      to_airport = "\n".join(textwrap.wrap(plane.route.get_route().get('to', '-'), width=12))
      draw.text((220, offset_top + 150), from_airport, font=self.font15, fill=self.epd.BLACK, align="center")
      draw.text((350, offset_top + 150), to_airport, font=self.font15, fill=self.epd.BLACK, align="center")

      # Render position data
      draw.text((460, offset_top + 50), f"Lat: {round(plane.lat, 4)} Lon: {round(plane.lon, 4)}", font=self.font15, fill=self.epd.BLACK)
      draw.text((460, offset_top + 70), f"{plane.speed}kt {plane.track}°", font=self.font15, fill=self.epd.BLACK)
      draw.text((460, offset_top + 90), f"{plane.altitude_in_feet}ft ({plane.vertical_rate}ft/min)", font=self.font15, fill=self.epd.BLACK)
      draw.text((460, offset_top + 110), f"Zuletzt gesehen:\n{plane.last_updated_at.strftime('%Y-%m-%d %H:%M:%S')}\nTotal: {plane.number_of_messages}", font=self.font15, fill=self.epd.BLACK)

      # Paste plane image if available
      if plane.image.get_image() is not None:
        rotated_image.paste(plane.image.get_image(), (0, offset_top))

      if index < 5:
        offset_top = 192 * (index+1)
        draw.line((0, offset_top, self.epd.height, offset_top), fill=self.epd.BLACK)
    
    self.image = rotated_image.rotate(90, expand=True)
    self.show_now()
    

  def show_now(self):
    if DUMMY_MONITOR:
      self.image.show()
    else:
      self.epd.init()
      self.epd.display(self.epd.getbuffer(self.image))
      time.sleep(3)
      self.epd.sleep()

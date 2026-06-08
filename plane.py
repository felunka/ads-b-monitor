import csv
import datetime
from config import *
import numpy as np
from coordinate_helper import calculate_distance, calculate_heading
from plane_image import PlaneImage
from plane_route import PlaneRoute
from message_type import MessageType
from surveillance_status import SurveillanceStatus
from wake_vortex_category import WakeVortexCategory

class Plane():

  def __init__(self, icao_addr: str, transponder_capability: int):
    self.icao_addr = icao_addr
    if self.icao_addr.startswith("0x"):
      self.icao_addr = self.icao_addr[2:]
    self.transponder_capability = transponder_capability

    # Image
    self.image = PlaneImage(self)
    # Route
    self.route = PlaneRoute(self)
    
    # DB data
    self.country = ""
    self.engines = ""
    self.icao_aircraft_class = ""
    self.manufacturer_name = ""
    self.model = ""
    self.operator_callsign = ""
    self.owner = ""
    self.registration = ""
    self.type_code = ""

    # Aircraft identification and category
    self.wake_vortex_category = WakeVortexCategory.NO_INFO
    self.callsign = ""

    # Airborne position
    self.surveillance_status = SurveillanceStatus.NO_CONDITION
    self.altitude_in_meters = -1
    self.altitude_in_feet = -1
    self.lat = -1
    self.lon = -1

    # Surface position and Airborne velocities
    self.speed = -1
    self.track = -1
    self.ground_lat = -1
    self.ground_lon = -1
    self.vertical_rate = 0

    self.last_updated_at = datetime.datetime.now()
    self.number_of_messages = 0
    
    self._read_db_data()

  def __hash__(self):
    return self.icao_addr

  def __eq__(self, other):
    if not isinstance(other, Plane):
      return False
    return self.icao_addr == other.icao_addr
  
  def __str__(self):
    return f"""
      ICAO:{self.icao_addr} Country:{self.country} Manufacturer:{self.manufacturer_name} Model:{self.model}
      Op Callsign:{self.operator_callsign} Owner:{self.owner} Registration:{self.registration} Type:{self.type_code}
      Callsign:{self.callsign} Cat:{self.wake_vortex_category}
      lat:{self.lat} lon:{self.lon}
      ground_lat:{self.ground_lat} ground_lon:{self.ground_lon}
      {self.altitude_in_feet}ft {self.altitude_in_meters}m {self.vertical_rate}ft/min
      speed:{self.speed}kt track:{self.track}
      Last seen: {self.last_updated_at} No messages: {self.number_of_messages}
    """
  
  def distance_and_direction_to_observer(self):
    dist_m = calculate_distance(OBSERVER_LAT, OBSERVER_LON, self.lat, self.lon)
    heading = calculate_heading(OBSERVER_LAT, OBSERVER_LON, self.lat, self.lon)

    return (dist_m, heading)
  
  def update(self, type_code: int, message_type: MessageType, message_data: str):
    self.last_updated_at = datetime.datetime.now()
    self.number_of_messages += 1

    if message_type == MessageType.AIRCRAFT_IDENTIFICATION:
      category_code = int(message_data[:3], 2)
      self.wake_vortex_category = WakeVortexCategory.from_codes(type_code, category_code)

      char_map = "#ABCDEFGHIJKLMNOPQRSTUVWXYZ##### ###############0123456789######"
      self.callsign = ""
      for i in range(8):
        start_index = 3 + i*6
        self.callsign += char_map[int(message_data[start_index:(start_index+6)], 2)]
      self.callsign = self.callsign.strip()
    elif message_type == MessageType.AIRBORNE_POSITION_BARO or message_type == MessageType.AIRBORNE_POSITION_GNSS:
      self.surveillance_status = SurveillanceStatus(int(message_data[:2], 2))

      if message_type == MessageType.AIRBORNE_POSITION_GNSS:
        self.altitude_in_meters = int(message_data[3:15], 2)
      else:
        """
        For barometric altitude, the 8th bit of the 12-bit altitude field is the Q bit. It indicates whether the altitude is
        encoded with an increment of 25 (Q=1) feet or 100 (Q=0) feet with Gillham code.
        """
        alt_bits = message_data[3:10] + message_data[11:15]
        q = message_data[10] == "1"

        if q:
          self.altitude_in_feet = (int(alt_bits, 2) * 25) - 1000
        else:
          # Too hard to parse encoding and only used by very old transponders
          pass

      # Position data
      is_odd = message_data[16] == "1"
      self.lat, self.lon = self._decode_cpr_local(
        lat_cpr=int(message_data[17:34], 2),
        lon_cpr=int(message_data[34:51], 2),
        is_odd=is_odd
      )
    elif message_type == MessageType.AIRBORNE_VELOCITIES:
      subtype = int(message_data[0:3], 2)
      if subtype in (1, 2):
        ew_raw = int(message_data[9:19], 2)
        ns_raw = int(message_data[20:30], 2)
        if ew_raw != 0 and ns_raw != 0:
          ew_vel = (ew_raw - 1) * (-1 if message_data[8] == "1" else 1)
          ns_vel = (ns_raw - 1) * (-1 if message_data[19] == "1" else 1)
          self.speed = round(np.sqrt(ew_vel**2 + ns_vel**2), 1)
          self.track = round(np.degrees(np.arctan2(ew_vel, ns_vel)) % 360, 2)
      elif subtype in (3, 4):
        if message_data[9] == "1":
          self.track = round(360 * int(message_data[10:20], 2) / 1024, 2)
        as_raw = int(message_data[21:31], 2)
        if as_raw != 0:
          self.speed = as_raw - 1
      vr_raw = int(message_data[32:41], 2)
      if vr_raw != 0:
        self.vertical_rate = (vr_raw - 1) * 64 * (-1 if message_data[31] == "1" else 1)
    if message_type == MessageType.SURFACE_POSITION:
      raw_speed = int(message_data[:7], 2)
      if raw_speed == 0:
        self.speed = -1
      elif raw_speed == 1:
        self.speed = 0
      elif raw_speed <= 8:
        self.speed = 0.125 + ((raw_speed - 2) * 0.125)
      elif raw_speed <= 12:
        self.speed = 1 + ((raw_speed - 9) * 0.25)
      elif raw_speed <= 38:
        self.speed = 2 + ((raw_speed - 13) * 0.5)
      elif raw_speed <= 93:
        self.speed = 15 + (raw_speed - 39)
      elif raw_speed <= 108:
        self.speed = 70 + ((raw_speed - 94) * 2)
      elif raw_speed <= 123:
        self.speed = 100 + ((raw_speed - 109) * 5)
      elif raw_speed <= 125:
        self.speed = 175
      
      # Check if ground track valid
      if message_data[7] == "1":
        self.track = 360 * int(message_data[8:15], 2) / 128
      
      is_odd = message_data[16] == "1"
      self.ground_lat, self.ground_lon = self._decode_cpr_local(
        lat_cpr=int(message_data[17:34], 2),
        lon_cpr=int(message_data[34:51], 2),
        is_odd=is_odd,
        surface=True
      )

  
  def _get_nl(self, lat):
    """Calculates the number of longitude zones for a given latitude."""
    if np.abs(lat) >= 87: return 1
    return int(np.floor((2 * np.pi) / (np.arccos(1 - (1 - np.cos(np.pi / 30)) / (np.cos(np.pi / 180 * lat)**2)))))

  def _decode_cpr_local(self, lat_cpr, lon_cpr, is_odd, surface=False):
    range_deg = 90 if surface else 360
    d_lat = range_deg / (4 * 15 - is_odd)
    
    # 1. Decode Latitude
    j = np.floor(REFERENCE_LAT / d_lat) + np.floor(0.5 + (REFERENCE_LAT % d_lat) / d_lat - lat_cpr / 2**CPR_BIT_RESOLUTION)
    lat = d_lat * (j + lat_cpr / 2**CPR_BIT_RESOLUTION)
    
    # 2. Decode Longitude
    nl = self._get_nl(lat) - is_odd
    if nl > 0:
      d_lon = range_deg / nl
    else:
      d_lon = range_deg
        
    m = np.floor(REFERENCE_LON / d_lon) + np.floor(0.5 + (REFERENCE_LON % d_lon) / d_lon - lon_cpr / 2**CPR_BIT_RESOLUTION)
    lon = d_lon * (m + lon_cpr / 2**CPR_BIT_RESOLUTION)
    
    return float(lat), float(lon)
  
  def _read_db_data(self):
    with open("data/aircraft-database-complete-2025-08.csv", mode="r", newline="") as csv_db:
      first_line = ""
      for index, line in enumerate(csv_db):
        if index == 0:
          first_line = line
        if line.startswith(self.icao_addr.lower()) or line.startswith(f"'{self.icao_addr.lower()}'"):
          csv_reader = csv.DictReader([first_line, line], delimiter=",", quotechar="'")
          row = next(csv_reader)
          
          self.country = row["country"]
          self.engines = row["engines"]
          self.icao_aircraft_class = row["icaoAircraftClass"]
          self.manufacturer_name = row["manufacturerName"] if row["manufacturerName"] else row["manufacturerIcao"]
          self.model = row["model"]
          self.operator_callsign = row["operatorCallsign"]
          self.owner = row["owner"]
          self.registration = row["registration"]
          self.type_code = row["typecode"]
          
          break

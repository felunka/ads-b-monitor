from config import *
from dump1090_reader import Dump1090Reader
from message_type import MessageType
from datetime import datetime
from coordinate_helper import calculate_distance
import time
import threading
from plane import Plane
from monitor import Monitor
from tester import CsvReplayReader

class DataHandler:

  def __init__(self):
    if DUMMY_MODE:
      self.reader = CsvReplayReader()
    else:
      self.reader = Dump1090Reader()
    self.plane_registry = {}

    self.monitor = Monitor()

    t = threading.Thread(target=self.reader.run)
    t.start()

    time.sleep(1)

    try:
      # Main application loop
      last_update_time = datetime.now()
      while True:
        if not self.reader.q.empty():
          msg = self.reader.q.get()
          self.parse_data(msg)
        else:
          time.sleep(1)
        
        # Check if time for monitor update
        if (datetime.now() - last_update_time).seconds > UPDATE_MONITOR_INTERVAL_SEC:
          # Clean registry
          self.plane_registry = {
            icao: plane
            for icao, plane
            in self.plane_registry.items()
            if (datetime.now() - plane.last_updated_at).seconds < MAX_PLANE_UPDATE_AGE_SEC
          }

          # Find 5 closest to reference point
          valid_planes = []
          for plane in self.plane_registry.values():
            print(plane)
            estimated_state = plane.get_estimated_state()
            if estimated_state["lat"] == -1 or estimated_state["lon"] == -1:
              continue
            if estimated_state["altitude_in_feet"] == -1 or estimated_state["altitude_in_feet"] >= PLANE_HIGHT_LIMIT:
              continue
            valid_planes.append((plane, estimated_state))

          top_5_planes = sorted(
              map(
                  lambda item: (
                    calculate_distance(
                      REFERENCE_LAT,
                      REFERENCE_LON,
                      item[1]["lat"],
                      item[1]["lon"]
                    ),
                    item[0]
                  ),
                  valid_planes
              ),
              key=lambda item: item[0]
          )[:5]

          # Render on monitor
          self.monitor.render_planes([plane for _, plane in top_5_planes])
          
          last_update_time = datetime.now()

    except KeyboardInterrupt:
      print("Stopping...")
    finally:
      try:
        self.reader.die()
        self.monitor.clear()
      except:
        pass
  

  
  def _hex_str_2_bin_str(self, data_hex):
    clean_hex = data_hex.lower().replace('0x', '').rstrip('l')
    clean_hex = clean_hex.zfill(28)  # 112 bits = 28 hex chars
    raw_bytes = bytes.fromhex(clean_hex)
    return "".join(f"{b:08b}" for b in raw_bytes)

  def fix_single_bit_error(self, data_bin):
    """
    Validate and attempt single-bit error correction on a 112-bit Mode-S message.
    Computes the CRC syndrome. If zero, the message is valid and returned as-is.
    If exactly one bit can be flipped to zero the syndrome, returns the corrected message.
    Otherwise returns None.
    """
    crc_val = 0
    for i in range(len(data_bin) - 24):
      if data_bin[i] == '1':
        crc_val ^= MODES_CHECKSUM_TABLE[i]
    syndrome = crc_val ^ int(data_bin[-24:], 2)

    if syndrome == 0:
      return data_bin

    data_list = list(data_bin)
    for i in range(len(data_bin) - 24):
      if MODES_CHECKSUM_TABLE[i] == syndrome:
        data_list[i] = '0' if data_list[i] == '1' else '1'
        return ''.join(data_list)

    return None

  def parse_data(self, data_hex):
    data_bin = self._hex_str_2_bin_str(data_hex)

    downlink_format = int(data_bin[:5], 2)
    if not (downlink_format & 0x10):
      return  # Discard 56-bit (short) messages

    type_code = int(data_bin[32:37], 2)
    message_type = MessageType.from_type_code(type_code)

    data_bin = self.fix_single_bit_error(data_bin)
    if data_bin is None:
      return

    transponder_capability = int(data_bin[5:8], 2)
    icao_addr = f'{int(data_bin[8:32], 2):x}'
    message_body = data_bin[37:-24]

    if icao_addr not in self.plane_registry:
      self.plane_registry[icao_addr] = Plane(icao_addr, transponder_capability)
    self.plane_registry[icao_addr].update(type_code, message_type, message_body)

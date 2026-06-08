from enum import Enum

class MessageType(Enum):
  """
  Code  Message type
  1-4 	Aircraft identification
  5-8 	Surface position
  9-18 	Airborne position (w/Baro Altitude)
  19 	  Airborne velocities
  20-22 Airborne position (w/GNSS Height)
  23-27 Reserved
  28 	  Aircraft status
  29 	  Target state and status information
  31 	  Aircraft operation status
  """
  AIRCRAFT_IDENTIFICATION = "AIRCRAFT_IDENTIFICATION"
  SURFACE_POSITION = "SURFACE_POSITION"
  AIRBORNE_POSITION_BARO = "AIRBORNE_POSITION_BARO"
  AIRBORNE_VELOCITIES = "AIRBORNE_VELOCITIES"
  AIRBORNE_POSITION_GNSS = "AIRBORNE_POSITION_GNSS"
  RESERVED = "RESERVED"
  AIRCRAFT_STATUS = "AIRCRAFT_STATUS"
  TARGET_STATE_AND_STATUS_INFORMATION = "TARGET_STATE_AND_STATUS_INFORMATION"
  AIRCRAFT_OPERATION_STATUS = "AIRCRAFT_OPERATION_STATUS"

  UNKNOWN = "UNKNOWN"

  @classmethod
  def from_type_code(cls, code):
    if 1 <= code <= 4:
      return cls.AIRCRAFT_IDENTIFICATION
    elif 5 <= code <= 8:
      return cls.SURFACE_POSITION
    elif 9 <= code <= 18:
      return cls.AIRBORNE_POSITION_BARO
    elif code == 19:
      return cls.AIRBORNE_VELOCITIES
    elif 20 <= code <= 22:
      return cls.AIRBORNE_POSITION_GNSS
    elif 23 <= code <= 27:
      return cls.RESERVED
    elif code == 28:
      return cls.AIRCRAFT_STATUS
    elif code == 29:
      return cls.TARGET_STATE_AND_STATUS_INFORMATION
    elif code == 31:
      return cls.AIRCRAFT_OPERATION_STATUS
    return cls.UNKNOWN

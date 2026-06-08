from enum import Enum

class WakeVortexCategory(Enum):
  """
  TC   CA   Category
  1    ANY  Reserved
  ANY  0    No category information
  2    1    Surface emergency vehicle
  2    2    Surface service vehicle
  2    3    Ground obstruction
  2    4-7  Reserved
  3    1    Glider, sailplane
  3    2    Lighter-than-air
  3    3    Parachutist, skydiver
  3    4    Ultralight, hang-glider, paraglider
  3    5    Reserved
  3    6    Unmanned aerial vehicle
  3    7    Space or transatmospheric vehicle
  4    1    Light (less than 7000 kg)
  4    2    Medium 1 (between 7000 kg and 34000 kg)
  4    3    Medium 2 (between 34000 kg to 136000 kg)
  4    4    High vortex aircraft
  4    5    Heavy (larger than 136000 kg)
  4    6    High performance (>5 g acceleration) and high speed (>400 kt)
  4    7    Rotorcraft
  """
  NO_INFO = "NO_INFO"
  SURFACE_EMERGENCY_VEHICLE = "SURFACE_EMERGENCY_VEHICLE"
  SURFACE_SERVICE_VEHICLE = "SURFACE_SERVICE_VEHICLE"
  GROUND_OBSTRUCTION = "GROUND_OBSTRUCTION"
  RESERVED = "RESERVED"
  GLIDER_SAILPLANE = "GLIDER_SAILPLANE"
  LIGHTER_THAN_AIR = "LIGHTER-THAN-AIR"
  PARACHUTIST_SKYDIVER = "PARACHUTIST_SKYDIVER"
  ULTRALIGHT_HANG_GLIDER_PARAGLIDER = "ULTRALIGHT_HANG-GLIDER_PARAGLIDER"
  UNMANNED_AERIAL_VEHICLE = "UNMANNED_AERIAL_VEHICLE"
  SPACE_OR_TRANSATMOSPHERIC_VEHICLE = "SPACE_OR_TRANSATMOSPHERIC_VEHICLE"
  LIGHT = "LIGHT"
  MEDIUM_1 = "MEDIUM_1"
  MEDIUM_2 = "MEDIUM_2"
  HIGH_VORTEX_AIRCRAFT = "HIGH_VORTEX_AIRCRAFT"
  HEAVY = "HEAVY"
  HIGH_PERFORMANCE_AND_HIGH_SPEED = "HIGH_PERFORMANCE_AND_HIGH_SPEED"
  ROTORCRAFT = "ROTORCRAFT"

  @classmethod
  def from_codes(cls, type_code, category_code):
    if type_code == 1:
      return cls.RESERVED
    elif category_code == 0:
      return cls.NO_INFO
    elif type_code == 2:
      if category_code == 1:
        return cls.SURFACE_EMERGENCY_VEHICLE
      elif category_code == 2:
        return cls.SURFACE_SERVICE_VEHICLE
      elif category_code == 3:
        return cls.GROUND_OBSTRUCTION
      elif 3 <= category_code <= 7:
        return cls.RESERVED
    elif type_code == 3:
      if category_code == 1:
        return cls.GLIDER_SAILPLANE
      elif category_code == 2:
        return cls.LIGHTER_THAN_AIR
      elif category_code == 3:
        return cls.PARACHUTIST_SKYDIVER
      elif category_code == 4:
        return cls.ULTRALIGHT_HANG_GLIDER_PARAGLIDER
      elif category_code == 5:
        return cls.RESERVED
      elif category_code == 6:
        return cls.UNMANNED_AERIAL_VEHICLE
      elif category_code == 7:
        return cls.SPACE_OR_TRANSATMOSPHERIC_VEHICLE
    elif type_code == 4:
      if category_code == 1:
        return cls.LIGHT
      elif category_code == 2:
        return cls.MEDIUM_1
      elif category_code == 3:
        return cls.MEDIUM_2
      elif category_code == 4:
        return cls.HIGH_VORTEX_AIRCRAFT
      elif category_code == 5:
        return cls.HEAVY
      elif category_code == 6:
        return cls.HIGH_PERFORMANCE_AND_HIGH_SPEED
      elif category_code == 7:
        return cls.ROTORCRAFT
    return cls.NO_INFO

from enum import Enum

class SurveillanceStatus(Enum):
  NO_CONDITION = 0
  PERMANENT_ALERT = 1
  TEMPORARY_ALERT = 2
  SPI_CONDITION = 3

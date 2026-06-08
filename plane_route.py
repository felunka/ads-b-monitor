import requests
from datetime import datetime, timezone

from config import FRA_RUNWAYS, RUNWAY_HALF_ANGLE_DEG, RUNWAY_HEADING_TOL_DEG, RUNWAY_MAX_DIST_M
from coordinate_helper import find_best_runway_match

class PlaneRoute:

  def __init__(self, plane):
    self.plane = plane
    self.route = {}
  
  def get_path(self):
    if self.plane.lat == -1 or self.plane.lon == -1 or self.plane.track == -1:
      return {}

    arrival = self.plane.vertical_rate <= 0
    match = find_best_runway_match(
      plane_lat=self.plane.lat,
      plane_lon=self.plane.lon,
      plane_heading=float(self.plane.track),
      runways=FRA_RUNWAYS,
      max_dist_m=RUNWAY_MAX_DIST_M,
      half_angle_deg=RUNWAY_HALF_ANGLE_DEG,
      heading_tol=RUNWAY_HEADING_TOL_DEG,
      arrival=arrival,
    )

    if not match:
      return {}

    return {
      "runway": match["name"],
      "arrival": match["arrival"],
      "cross_m": match["cross_m"],
      "along_m": match["along_m"],
    }

  def get_route(self):
    if "flight_no" in self.route:
      return self.route
    
    # Search FRA arrival API for flight
    for page_no in range(-3, 3):
      url = f"https://www.frankfurt-airport.com/en/_jcr_content.flights.json/filter?perpage=50&flighttype=arrivals&page={page_no}"
      result = requests.get(url)
      if result.status_code == 200 and "data" in result.json():
        for flight in result.json()["data"]:
          if flight["reg"].upper() == self.plane.registration.replace("-", "").upper():
            scheduled_time = datetime.strptime(flight["sched"], "%Y-%m-%dT%H:%M:%S%z")
            if abs((datetime.now(timezone.utc) - scheduled_time).total_seconds()) < 2700:
              self.route = {
                "flight_no": flight["fnr"],
                "to_iata": "FRA",
                "to": "Flughafen Frankfurt",
                "from_iata": flight["iata"],
                "from": flight["apname"]
              }
            return self.route

    # Search FRA departure API for flight
    for page_no in range(-3, 3):
      url = f"https://www.frankfurt-airport.com/en/_jcr_content.flights.json/filter?perpage=50&flighttype=departures&page={page_no}"
      result = requests.get(url)
      if result.status_code == 200 and "data" in result.json():
        for flight in result.json()["data"]:
          if flight["reg"].upper() == self.plane.registration.replace("-", "").upper():
            scheduled_time = datetime.strptime(flight["sched"], "%Y-%m-%dT%H:%M:%S%z")
            if abs((datetime.now(timezone.utc) - scheduled_time).total_seconds()) < 2700:
              self.route = {
                "flight_no": flight["fnr"],
                "from_iata": "FRA",
                "from": "Flughafen Frankfurt",
                "to_iata": flight["iata"],
                "to": flight["apname"]
              }
            return self.route

    return {}

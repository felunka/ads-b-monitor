import math

from plane import Plane
from monitor import Monitor
from config import EARTH_RADIUS, FRA_RUNWAYS, RUNWAY_HALF_ANGLE_DEG
from coordinate_helper import find_best_runway_match, is_on_final_cone

def make_point_from_runway_offset(runway, along_m, cross_m, arrival=True):
  axis_heading = runway["heading"] + 180 if arrival else runway["heading"]
  axis_angle = math.radians(axis_heading)

  # Inverse rotation of to_runway_coords.
  lat_m = math.cos(axis_angle) * along_m - math.sin(axis_angle) * cross_m
  lon_m = math.sin(axis_angle) * along_m + math.cos(axis_angle) * cross_m

  lat = runway["lat"] + math.degrees(lat_m / EARTH_RADIUS)
  lon = runway["lon"] + math.degrees(lon_m / (EARTH_RADIUS * math.cos(math.radians(runway["lat"]))))
  return lat, lon

planes = []
plane_data = [("3c6445", "DLH1KN"), ("71c227", "TWB403"), ("3c7a4c", "CFG038"), ("4cc52e", "ICE520"), ("01023a", "MSC2942")]

target_runway = next(r for r in FRA_RUNWAYS if r["name"] == "25C")

# Distances are in meters, all inside a 3 degree cone: abs(cross) < along * tan(3deg)
offsets = [
  (3000, 50),
  (5500, -80),
  (8000, 130),
  (11000, -170),
  (14000, 200),
]

for index, (icao, callsign) in enumerate(plane_data):
  along_m, cross_m = offsets[index]
  p = Plane(icao, 1)
  p.callsign = callsign

  p.lat, p.lon = 50.052, 8.636
  p.track = float((target_runway["heading"] + (-3 + index)) % 360)
  p.vertical_rate = -700

  planes.append(p)

for plane in planes:
  in_cone = is_on_final_cone(
    plane_lat=plane.lat,
    plane_lon=plane.lon,
    plane_heading=plane.track,
    rwy_lat=target_runway["lat"],
    rwy_lon=target_runway["lon"],
    rwy_heading=target_runway["heading"],
    half_angle_deg=RUNWAY_HALF_ANGLE_DEG,
    arrival=True,
  )
  best = find_best_runway_match(
    plane_lat=plane.lat,
    plane_lon=plane.lon,
    plane_heading=plane.track,
    runways=FRA_RUNWAYS,
    half_angle_deg=RUNWAY_HALF_ANGLE_DEG,
    arrival=True,
  )
  print(f"{plane.callsign}: in_cone={in_cone} best_runway={best['name'] if best else '-'}")




m = Monitor()
m.render_planes(planes)

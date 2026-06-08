import math
from config import EARTH_RADIUS

def calculate_distance(lat1, lon1, lat2, lon2):
  # Convert decimal degrees to radians
  phi1, phi2 = math.radians(lat1), math.radians(lat2)
  delta_phi = math.radians(lat2 - lat1)
  delta_lambda = math.radians(lon2 - lon1)
  
  # Haversine formula
  a = math.sin(delta_phi / 2)**2 + \
    math.cos(phi1) * math.cos(phi2) * \
    math.sin(delta_lambda / 2)**2
  c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
  
  return EARTH_RADIUS * c  # Distance in meters

def calculate_heading(origin_lat, origin_lon, target_lat, target_lon):
  phi1 = math.radians(origin_lat)
  phi2 = math.radians(target_lat)
  delta_lambda = math.radians(target_lon - origin_lon)

  y = math.sin(delta_lambda) * math.cos(phi2)
  x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)

  heading = math.degrees(math.atan2(y, x))
  return float((heading + 360) % 360)

def to_runway_coords(plane_lat, plane_lon, rwy_lat, rwy_lon, rwy_heading_deg, arrival=True):
  dlat = math.radians(plane_lat - rwy_lat)
  dlon = math.radians(plane_lon - rwy_lon)
  lat_m  = dlat * EARTH_RADIUS
  lon_m  = dlon * EARTH_RADIUS * math.cos(math.radians(rwy_lat))

  axis_heading = rwy_heading_deg + 180 if arrival else rwy_heading_deg
  axis_angle = math.radians(axis_heading)
  along  =  math.cos(axis_angle) * lat_m + math.sin(axis_angle) * lon_m
  cross  = -math.sin(axis_angle) * lat_m + math.cos(axis_angle) * lon_m

  return along, cross

def is_on_final_cone(plane_lat, plane_lon, plane_heading,
           rwy_lat, rwy_lon, rwy_heading,
           max_dist_m=30_000, half_angle_deg=3, heading_tol=20, arrival=True):

  hdg_diff = abs((plane_heading - rwy_heading + 180) % 360 - 180)
  if hdg_diff > heading_tol:
    return False

  along, cross = to_runway_coords(plane_lat, plane_lon, rwy_lat, rwy_lon, rwy_heading, arrival=arrival)

  if not (0 < along < max_dist_m):
    return False

  # Width of cone at this distance
  max_cross = along * math.tan(math.radians(half_angle_deg))
  return abs(cross) < max_cross

def find_best_runway_match(plane_lat, plane_lon, plane_heading, runways,
                max_dist_m=30_000, half_angle_deg=3, heading_tol=20, arrival=True):
  best = None
  best_cross = float("inf")

  for runway in runways:
    hdg_diff = abs((plane_heading - runway["heading"] + 180) % 360 - 180)
    if hdg_diff > heading_tol:
      continue

    along, cross = to_runway_coords(
      plane_lat,
      plane_lon,
      runway["lat"],
      runway["lon"],
      runway["heading"],
      arrival=arrival,
    )

    if not (0 < along < max_dist_m):
      continue

    max_cross = along * math.tan(math.radians(half_angle_deg))
    abs_cross = abs(cross)
    if abs_cross < max_cross and abs_cross < best_cross:
      best_cross = abs_cross
      best = {
        "name": runway["name"],
        "heading": runway["heading"],
        "threshold_lat": runway["lat"],
        "threshold_lon": runway["lon"],
        "along_m": round(along, 1),
        "cross_m": round(cross, 1),
        "arrival": arrival,
      }

  return best
from io import BytesIO
from PIL import Image
import requests

EPD_COLORS_RGB = [
  (0, 0, 0),       # BLACK
  (255, 255, 255), # WHITE
  (255, 255, 0),   # YELLOW
  (255, 0, 0),     # RED
]

class PlaneImage:

  def __init__(self, plane):
    self.plane = plane
    self.image = None
  
  def get_image(self):
    if self.image is not None:
      return self.image
    
    if self.plane.registration is None or self.plane.registration == "":
      return None
    url = f"https://api.planespotters.net/pub/photos/reg/{self.plane.registration}"
    result = requests.get(url, headers={"User-Agent": "ADS-B Display (admin@felunka.de)"})
    if result.status_code == 200 and len(result.json()['photos']) > 0:
      pic_url = result.json()['photos'][0]['thumbnail']['src']
      pic_result = requests.get(pic_url)
      if pic_result.status_code == 200:
        downloaded_pic = Image.open(BytesIO(pic_result.content)).convert("RGB")
        self.image = self.to_epd_4color(downloaded_pic)

        return self.image

  def to_epd_4color(self, img, size=None):
    # Optional: resize to panel resolution first
    if size is not None:
      img = img.resize(size, Image.Resampling.LANCZOS)

    # Build a PIL palette
    pal_img = Image.new("P", (1, 1))
    flat_palette = []
    for c in EPD_COLORS_RGB:
      flat_palette.extend(c)

    # PIL palette requires 256 colors (768 values), pad the rest
    flat_palette.extend([0] * (768 - len(flat_palette)))
    pal_img.putpalette(flat_palette)

    return img.quantize(
      palette=pal_img,
      dither=Image.Dither.FLOYDSTEINBERG
    )

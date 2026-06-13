import time
from PIL import Image, ImageDraw, ImageFont

from display_lib import EPD


def make_counter_patch(value):
  # 1-bit patch: white background, black text.
  patch = Image.new("1", (240, 72), 1)
  draw = ImageDraw.Draw(patch)
  font = ImageFont.load_default()
  draw.text((8, 8), f"Counter: {value:02d}", fill=0, font=font)
  return patch


def main():
  epd = EPD()
  epd.init()

  try:
    # Fixed top-left location for partial update test.
    x = 560
    y = 24

    for i in range(10):
      patch = make_counter_patch(i)
      ok = epd.partial_bw_test(patch, x=x, y=y, write_red_plane=False)
      print(f"update {i}: {'ok' if ok else 'skipped'}")
      time.sleep(1)
  finally:
    epd.sleep()


if __name__ == "__main__":
  main()

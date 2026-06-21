import csv
import queue
import re
import time


class CsvReplayReader:

  def __init__(self, csv_path: str = "data/test_adsb.csv"):
    self.q = queue.Queue()
    self.csv_path = csv_path
    self._running = True
    self._msg_pattern = re.compile(r"^[0-9a-fA-F]{14,28}$")

  def _sleep_interruptible(self, delay_s: float):
    remaining = max(0.0, delay_s)
    while self._running and remaining > 0:
      step = min(0.2, remaining)
      time.sleep(step)
      remaining -= step

  def run(self):
    while self._running:
      previous_ts = None
      try:
        with open(self.csv_path, mode="r", newline="") as csv_file:
          csv_reader = csv.reader(csv_file)
          for row in csv_reader:
            if not self._running:
              return
            if len(row) < 2:
              continue

            try:
              current_ts = float(row[0])
            except ValueError:
              continue

            message_hex = row[1].strip()
            if not self._msg_pattern.fullmatch(message_hex):
              continue

            if previous_ts is not None and current_ts > previous_ts:
              self._sleep_interruptible(current_ts - previous_ts)

            self.q.put(message_hex)
            previous_ts = current_ts
      except FileNotFoundError:
        # Keep trying until the replay file becomes available.
        self._sleep_interruptible(1.0)

  def die(self):
    self._running = False

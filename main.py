import signal
import sys
from data_handler import DataHandler

def _handle_sigterm(signum, frame):
  raise KeyboardInterrupt

signal.signal(signal.SIGTERM, _handle_sigterm)

DataHandler()

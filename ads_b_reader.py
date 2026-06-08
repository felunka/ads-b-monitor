from rtlsdr import *
from config import *
import numpy as np
import queue
import time

_EXPECTED_CB_INTERVAL = MODES_DATA_LEN / 2 / SAMPLE_RATE  # seconds per buffer

class AdsBReader:

  def __init__(self):
    self.q = queue.Queue()
    self._last_cb_time = None
    self._dropped_buffers = 0

    self.sdr = RtlSdr()
    self.sdr.DEFAULT_ASYNC_BUF_NUMBER = MODES_ASYNC_BUF_NUMBER

    self.sdr.sample_rate = SAMPLE_RATE # Hz
    self.sdr.center_freq = 109e7   # Hz
    self.sdr.gain = 40
    self.sdr.set_agc_mode(0)

  def _preamble_signal_strength(self, sig):
    """
    Calculate the signal strength from the min and max of the preamble samples normalized on range, expressed in %
    """
    return round(((max(sig[0:14]) - min(sig[0:14])) / float(MODES_SIGMAX)) * 100, 1)

  def _data_to_long(self, msg):
    """
    Convert samples into bits assuming manchester coding (high to low is 1, low to high is 0)
    """
    bits = 0
    for ind in range(MODES_DATA_OFFSET, len(msg), 2):
      bits = (bits << 1) | (1 if msg[ind] > msg[ind + 1] else 0)
    return bits

  def _detect_preamble(self, sig, ind):
    """
    Detects a preamble from sig
    
    The preamble should ideally look like this

    high      *   *         *   *     
              *   *         *   *     
    low       * * * * * * * * * * *  *  *  *  * 
    bit nr    0 1 2 3 4 5 6 7 8 9 10 11 12 13 14
    """

    if sig[ind + 0] > sig[ind + 1] \
      and sig[ind + 1] < sig[ind + 2] \
      and sig[ind + 2] > sig[ind + 3] \
      and sig[ind + 3] < sig[ind + 0] \
      and sig[ind + 4] < sig[ind + 0] \
      and sig[ind + 5] < sig[ind + 0] \
      and sig[ind + 6] < sig[ind + 0] \
      and sig[ind + 7] > sig[ind + 8] \
      and sig[ind + 8] < sig[ind + 9] \
      and sig[ind + 9] > sig[ind + 6]:

      high = (sig[ind + 0] + sig[ind + 2] + sig[ind + 7] + sig[ind + 9]) / 6
      if sig[ind + 4] < high \
          and sig[ind + 5] < high \
          and sig[ind + 11] < high \
          and sig[ind + 12] < high \
          and sig[ind + 13] < high \
          and sig[ind + 14] < high:
        return True
    return False

  def _detect_adsb(self, sig):
    arr = []
    max_length = len(sig) - SQUITTER_LONG_MAX_SIZE
    ind = 0
    while ind < max_length:
      if self._detect_preamble(sig, ind):
        sig_strength = self._preamble_signal_strength(sig[ind: ind + PREAMBLE_SAMPLES])
        arr.append([sig_strength, sig[ind:ind + SQUITTER_LONG_MAX_SIZE]])

        # Determine if we have found a long or short squitter and increment ind accordingly
        msg = self._data_to_long(sig[ind:ind + SQUITTER_LONG_MAX_SIZE])
        downlink_format = (int(hex(msg)[2:4], base=16) & 0xF8) >> 3
        if downlink_format & 0x10:
          ind += SQUITTER_LONG_MAX_SIZE
        else:
          ind += SQUITTER_SHORT_MAX_SIZE
        continue

      ind += 1
    # NB _data_to_long transformation will skip the preamble samples
    return [[arr[ind][0], self._data_to_long(arr[ind][1])] for ind in range(len(arr))]

  def _iq_to_uint(self, sig):
    # Convert input to a numpy array if it isn't one
    sig = np.asarray(sig, dtype=np.uint16)
    
    # Extract I and Q components
    i = (sig >> 8).astype(np.float32) # Same as / 256
    q = (sig & 0xFF).astype(np.float32) # Same as % 256
    
    # Calculate magnitude using the same constants from your snippet
    # Distance formula: sqrt((i*2-255)^2 + (q*2-255)^2)
    mag = 258.433254 * np.sqrt((i * 2 - 255)**2 + (q * 2 - 255)**2) - 365.4798
    
    # Round, clip (clamp), and convert to integer
    return np.clip(np.round(mag), 0, MODES_SIGMAX).astype(np.uint16)

  def _sdr_cb(self, samples, context):
    now = time.monotonic()
    if self._last_cb_time is not None:
      gap = now - self._last_cb_time
      if gap > _EXPECTED_CB_INTERVAL * 1.5:
        dropped = round(gap / _EXPECTED_CB_INTERVAL) - 1
        self._dropped_buffers += dropped
        print(f"[WARN] Gap {gap*1000:.1f}ms — ~{dropped} buffer(s) dropped (total: {self._dropped_buffers})")
    self._last_cb_time = now

    samples_np = np.frombuffer(samples, dtype=np.uint8)
    samples = samples_np[0::2].astype(np.uint16) | (samples_np[1::2].astype(np.uint16) << 8)

    samples = self._iq_to_uint(samples)

    adsb_samples = self._detect_adsb(samples)  # This is where we scan for the preamble
    if not self.q.full():
      self.q.put(adsb_samples)

  def run(self):
    print("Started run")
    self.sdr.read_bytes_async(self._sdr_cb, num_bytes=MODES_DATA_LEN)

  def die(self):
    self.sdr.cancel_read_async()
    self.sdr.close()

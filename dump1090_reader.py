import queue
import re
import signal
import subprocess

class Dump1090Reader:

  def __init__(self):
    self.q = queue.Queue()
    self.process = None

  def run(self):
    pattern = re.compile(r'^\*([0-9a-f]{14,28});$')
    self.process = subprocess.Popen(
      ["../dump1090/dump1090", "--raw", "--aggressive"],
      stdout=subprocess.PIPE,
      stderr=subprocess.DEVNULL,
      text=True
    )
    for line in self.process.stdout:
      m = pattern.match(line.rstrip("\n"))
      if m:
        self.q.put(m.group(1))

  def die(self):
    if self.process is not None:
      self.process.send_signal(signal.SIGINT)
      self.process.wait()

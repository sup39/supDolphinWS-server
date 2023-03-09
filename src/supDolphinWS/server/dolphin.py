# SPDX-License-Identifier: MIT
# Copyright (c) 2023 sup39
import os
import psutil
import struct
from multiprocessing.shared_memory import SharedMemory

MEM1_START = 0x80000000
MEM1_END   = 0x81800000
MEM2_START = 0x90000000
MEM2_END   = 0x93000000
MEM2_OFFSET = 0x4040000

dolphinProcNames = \
  {'Dolphin.exe', 'DolphinQt2.exe', 'DolphinWx.exe'} if os.name == 'nt' \
  else {'dolphin-emu', 'dolphin-emu-qt2', 'dolphin-emu-wx'}

def try_get_memory(pid):
  try: return SharedMemory('dolphin-emu.'+str(pid))
  except FileNotFoundError: return None

def find_memory(exclude_pid={}):
  try: return next(
    (p.pid, m)
    for p in psutil.process_iter(['pid', 'name'])
    if p.pid not in exclude_pid and p.name() in dolphinProcNames
    for m in [try_get_memory(p.pid)]
    if m is not None
  )
  except StopIteration: return None

class Dolphin():
  def __init__(self):
    self.pid = None
    self.m = None
  def hook(self, exclude_pid={}):
    r = find_memory(exclude_pid)
    if r is None: return
    ## success
    self.pid, self.m = r
    return r
  def unhook(self):
    self.pid = None
    if self.m is not None:
      self.m.close()
      self.m = None
  def _read_bytes(self, addr, size):
    '''
      addr: int
      size: int
    '''
    if MEM1_START <= addr <= MEM1_END-size:
      idx = addr-MEM1_START
    elif MEM2_START <= addr <= MEM2_END-size and len(self.m) > MEM2_OFFSET:
      idx = MEM2_OFFSET + addr-MEM2_START
    else: return None
    return self.m.buf[idx:idx+size].tobytes()
  def _write_bytes(self, addr, payload):
    '''
      addr: int
      payload: bytes
    '''
    size = len(payload)
    if MEM1_START <= addr <= MEM1_END-size:
      idx = addr-MEM1_START
    elif MEM2_START <= addr <= MEM2_END-size and len(self.m) > MEM2_OFFSET:
      idx = MEM2_OFFSET + addr-MEM2_START
    else: return None
    self.m.buf[idx:idx+size] = payload
    return addr
  def resolve_addr(self, addr):
    '''
      addr: int|int[]
    '''
    offs = [addr] if isinstance(addr, int) else addr
    addr = 0
    for off in offs[:-1]:
      raw = self._read_bytes(addr+off, 4)
      if raw is None: return None
      addr, = struct.unpack('>I', raw)
    return addr + (offs[-1] if len(offs) else 0)
  def read_bytes(self, addr, size):
    '''
      addr: int|int[]
      size: int
    '''
    return self._read_bytes(self.resolve_addr(addr), size)
  def write_bytes(self, addr, payload):
    '''
      addr: int|int[]
      payload: bytes
    '''
    return self._write_bytes(self.resolve_addr(addr), payload)

# SPDX-License-Identifier: MIT
# Copyright (c) 2023 sup39
'''
The `try_get_memory` function is based on
  `WindowsDolphinProcess::obtainEmuRAMInformations()`
  (https://github.com/aldelaro5/Dolphin-memory-engine/blob/master/Source/DolphinProcess/Windows/WindowsDolphinProcess.cpp#L47)
from aldelaro5's Dolphin memory engine
  (https://github.com/aldelaro5/Dolphin-memory-engine)
# SPDX-License-Identifier: MIT
# Copyright (c) 2017 aldelaro5
'''

import ctypes
from ctypes import wintypes
wintypes.SIZE_T = ctypes.c_uint32 if ctypes.sizeof(ctypes.c_void_p) == 4 else ctypes.c_uint64

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
MEM_MAPPED = 0x40000

class MEMORY_BASIC_INFORMATION(ctypes.Structure):
  _fields_ = [
    ("BaseAddress", wintypes.LPVOID),
    ("AllocationBase", wintypes.LPVOID),
    ("AllocationProtect", wintypes.DWORD),
    ("RegionSize", wintypes.SIZE_T),
    ("State", wintypes.DWORD),
    ("Protect", wintypes.DWORD),
    ("Type", wintypes.DWORD)
  ]

kernel32 = ctypes.WinDLL("kernel32.dll")
virtual_query_ex = kernel32.VirtualQueryEx
virtual_query_ex.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, ctypes.POINTER(MEMORY_BASIC_INFORMATION), wintypes.SIZE_T]
virtual_query_ex.restype = wintypes.SIZE_T

class FakeMemorySlice(bytes):
  def tobytes(self): return self

class ProcessMemoryView:
  def __init__(self, hProcess, baseAddr):
    self.hProcess = hProcess
    self.baseAddr = baseAddr
  def __getitem__(self, rg):
    if type(rg) is not slice: raise TypeError('Index must be `slice`')
    assert rg.start is not None and rg.stop is not None, 'Start and stop of the slice must be given'
    addr = rg.start
    size = rg.stop - rg.start
    buf = ctypes.create_string_buffer(size)
    nbyte = ctypes.c_size_t(0)
    assert kernel32.ReadProcessMemory(
      self.hProcess,
      ctypes.c_void_p(self.baseAddr+addr),
      buf,
      ctypes.c_size_t(size),
      ctypes.byref(nbyte),
    ), f'Failed to read process memory. Error code: {kernel32.GetLastError()}'
    return FakeMemorySlice(buf[slice(None, None, rg.step)])
  def __setitem__(self, rg, payload):
    if type(rg) is not slice: raise TypeError('Index must be `slice`')
    assert rg.start is not None, 'Start of the slice must be given'
    addr = rg.start
    nbyte = ctypes.c_size_t(0)
    assert kernel32.WriteProcessMemory(
      self.hProcess,
      ctypes.c_void_p(self.baseAddr+addr),
      bytes(payload),
      ctypes.c_size_t(len(payload)),
      ctypes.byref(nbyte)
    ), f'Failed to write process memory. Error code: {kernel32.GetLastError()}'
    return nbyte.value
  def __len__(self):
    return 0x2000000 # TODO

class FakeSharedMemory:
  def __init__(self, hProcess, baseAddr):
    self.hProcess = hProcess
    self.buf = ProcessMemoryView(hProcess, baseAddr)
  def __del__(self):
    self.close()
  def close(self):
    kernel32.CloseHandle(self.hProcess)

def try_get_memory(pid): # TODO MEM2
  hProcess = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ | PROCESS_VM_WRITE, False, pid)
  baseAddr = 0
  memory_info = MEMORY_BASIC_INFORMATION()
  while virtual_query_ex(hProcess, baseAddr, ctypes.byref(memory_info), ctypes.sizeof(memory_info)):
    if memory_info.RegionSize == 0x2000000 and memory_info.Type == MEM_MAPPED:
      return FakeSharedMemory(hProcess, baseAddr)
    baseAddr += memory_info.RegionSize

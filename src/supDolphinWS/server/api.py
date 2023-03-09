# SPDX-License-Identifier: MIT
# Copyright (c) 2023 sup39
VERSION = '0.1.0'

import struct
from .err import abort, ERR_DOLPHIN, ERR_BAD_REQ
from .dolphin import Dolphin

_d = Dolphin()
def get_dolphin():
  if _d.m is None:
    r = _d.hook()
    if r is None: abort(ERR_DOLPHIN, 'Fail to find shared memory. Is the game running on Dolphin?')
  return _d

def get_version(body):
  return VERSION.encode()

def do_hook(body):
  _d.unhook()
  get_dolphin()
  return b''

'''
u32   size
u32   base
s32[] addr segments
'''
def read_ram(body):
  nbody = len(body)
  if nbody < 4 or nbody % 4: abort(ERR_BAD_REQ, 'Bad payload')
  ## args
  size, = struct.unpack('>I', body[:4])
  addr = [
    MEM1_START if nbody < 8 else struct.unpack('>I', body[4:8])[0],
    *(p[0] for p in struct.iter_unpack('>i', body[8:])),
  ]
  ## access
  d = get_dolphin()
  return d.read_bytes(addr, size) or b''

'''
u32   size
u8[]  content
u32   base
s32[] addr segments
'''
def write_ram(body):
  nbody = len(body)
  if nbody < 4: abort(ERR_BAD_REQ, 'Bad payload')
  ## size
  size, = struct.unpack('>I', body[:4])
  i = 4+size
  if nbody < i: abort(ERR_BAD_REQ, 'Bad payload')
  content = body[4:i]
  ## addr
  if (nbody-i) % 4: abort(ERR_BAD_REQ, 'Bad payload')
  addr = [
    MEM1_START if nbody == i else struct.unpack('>I', body[i:i+4])[0],
    *(p[0] for p in struct.iter_unpack('>i', body[i+4:])),
  ]
  ## access
  d = get_dolphin()
  a = d.write_bytes(addr, content)
  return b'' if a is None else struct.pack('>I', a)

handlers = {
  0x00: get_version,
  0x01: do_hook,
  0x02: read_ram,
  0x03: write_ram,
}

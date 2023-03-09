# SPDX-License-Identifier: MIT
# Copyright (c) 2023 sup39
def tryParseInt(x, radix=10):
  try:
    return int(x, radix)
  except ValueError:
    return None

def parseAddrPath(s):
  if s == '': return [MEM1_START]
  try:
    return [
      int(ch, 16)
      for ch in s.split('/')
    ]
  except ValueError:
    return None

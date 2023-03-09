# SPDX-License-Identifier: MIT
# Copyright (c) 2023 sup39

ERR_UNKNOWN = 255
ERR_CMD_NOT_FOUND = 254
ERR_DOLPHIN = 253
ERR_BAD_REQ = 252

class ErrorResponse(Exception):
  def __init__(self, code, payload):
    self.code = code
    self.payload = payload
def abort(code, payload=''):
  raise ErrorResponse(code, payload)

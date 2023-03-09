# SPDX-License-Identifier: MIT
# Copyright (c) 2023 sup39
from wsocket import WSocketApp, run as _run
from .utils import tryParseInt, parseAddrPath
from .api import VERSION, handlers, _d
from .err import *

'''
u32 id
u8  cmdtype
'''
def on_message(msg, client):
  if type(msg) != bytearray: return
  if len(msg) < 5: return
  ID, cmdtype, body = msg[:4], msg[4], msg[5:]
  handler = handlers.get(cmdtype)
  if handler is None:
    return client.send(ID+struct.pack('>B', ERR_CMD_NOT_FOUND))
  try:
    res = handler(body)
    code = 0
    if res is None:
      code = ERR_UNKNOWN
      res = b''
  except ErrorResponse as err:
    code, res = err.code, err.payload.encode()
  client.send(ID+code.to_bytes(1, 'big')+res)

class MyWSocketApp(WSocketApp):
  def wsgi(self, environ, start_response):
    wsock = environ.get("wsgi.websocket")
    ## plain HTTP
    if not wsock:
      start_response()
      return '<h1>supDolphinWSServer</h1>'
    ## WebSocket
    self.onconnect(wsock)
    while True:
      try:
        message = wsock.receive()
        if message != None:
          self.onmessage(message, wsock)
      except WebSocketError as e:
          break
    return []

def run(args):
  app = WSocketApp()
  app.onmessage += on_message
  _d.hook()
  _run(app, host=args.host, port=args.port)

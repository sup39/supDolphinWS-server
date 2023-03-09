# SPDX-License-Identifier: MIT
# Copyright (c) 2023 sup39
import argparse
from .server import run, VERSION

if __name__ == '__main__':
  parser = argparse.ArgumentParser(prog='python -m supDolphinWS.server', add_help=False)
  parser.add_argument('-h', '--host', default='localhost', help='the IP address that the server will listen on')
  parser.add_argument('-p', '--port', default=35353, type=int, help='the port number that the server will listen on')
  parser.add_argument('--exclude-pids', default=[], nargs='*', help='the pid list to exclude when finding dolphin')
  parser.add_argument('-?', '--help', action='help', default=argparse.SUPPRESS, help='show this help message and exit')
  parser.add_argument('--version', action='store_true', help='show the version of the server')
  args = parser.parse_args()
  if args.version:
    print(VERSION)
  else:
    run(args)

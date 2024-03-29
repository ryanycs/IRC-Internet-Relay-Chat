#!/usr/bin/env python3
import argparse

from client import Client
from server import Server

if __name__ == "__main__":
    choices = {"client": Client, "server": Server}
    parser = argparse.ArgumentParser()
    parser.add_argument("role", choices=choices)
    parser.add_argument(
        "host",
        help="interface the server listens at;" " host the client sends to",
    )
    parser.add_argument(
        "-p", metavar="PORT", type=int, default=6667, help="TCP port (default 6667)"
    )
    args = parser.parse_args()
    role = choices[args.role](args.host, args.p)
    role.start()

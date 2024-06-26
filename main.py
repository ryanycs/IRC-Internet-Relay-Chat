#!/usr/bin/env python3
import argparse
import json
import logging
import re
import socket
import threading
import time


class User:
    def __init__(self, username: str, conn: socket.socket):
        self.username = username
        self.conn = conn


class Server:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.clients = {}  # {addr: {"conn": conn, "username": None}}
        self.commands = {
            "/USER": self.command_user,
            "/WHO": self.command_who,
            "/QUIT": self.command_quit,
        }

    def send_message(self, conn: socket.socket, username: str, message: str):
        """
        Sends a message to the client
        """
        data = json.dumps(
            {
                "time": time.strftime("%H:%M:%S"),
                "username": username,
                "message": message,
            }
        ).encode("utf-8")
        conn.send(data)

    def command_user(self, conn: socket.socket, addr: tuple, message: str):
        """
        Extracts the username from the message and adds it to the list of clients
        """
        # extract username from message
        username = re.match("^\/USER\s*(.*)", message).group(1)
        # add user to list of users
        self.clients[addr]["username"] = username
        # notify all connected clients that a new user has joined
        for client_addr in self.clients:
            if client_addr != addr:
                self.send_message(
                    self.clients[client_addr]["conn"],
                    "-->",
                    f"{username} has joined #public.",
                )

    def command_who(self, conn: socket.socket, addr: tuple, message: str):
        """
        Sends a list of all connected clients to the client
        """
        tmpstr = []
        for client in self.clients:
            if self.clients[client]["username"] is not None:
                tmpstr.append(
                    f"{self.clients[client]['username']}\t{client}\t['#public']"
                )
        message = "USER FROM CHANNEL\n" + "\n".join(tmpstr)
        conn.send(
            json.dumps(
                {
                    "username": "SERVER",
                    "message": message,
                }
            ).encode("utf-8")
        )

    def command_quit(self, conn: socket.socket, addr: tuple, message: str):
        """
        Closes the connection with the client
        """
        match_obj = re.match("/QUIT\s*(.*)", message)
        message = match_obj.group(1) if match_obj else None

        # notify all connected clients that a user has left
        for client_addr in self.clients:
            if client_addr == addr:
                continue
            if message:
                # send quit message
                self.send_message(self.clients[client_addr]["conn"], "-->", message)
            self.send_message(
                self.clients[client_addr]["conn"],
                "-->",
                f"{self.clients[addr]['username']} has left #public.",
            )

        conn.close()
        self.clients.pop(addr)

    def handle_client(self, conn: socket.socket, addr: tuple):
        """
        Handles a new client connection
        """
        print(f"New connection from {addr}")

        while True:
            # check if connection is still open
            if conn.fileno() == -1:
                break

            data = conn.recv(1024)
            if not data:
                break
            data = json.loads(data.decode("utf-8"))
            message = data["message"]

            match_obj = re.match("/[A-Z]+", message)
            command = match_obj.group() if match_obj else None
            if command in self.commands.keys():
                # execute command
                self.commands[command](conn, addr, message)
            else:
                # check if user has set a username
                if self.clients[addr]["username"] is None:
                    self.send_message(conn, "-->", "Please set a username first.")
                    continue
                # broadcast message to all connected clients
                for client_addr in self.clients:
                    if client_addr != addr:
                        self.send_message(
                            self.clients[client_addr]["conn"],
                            self.clients[addr]["username"],
                            message,
                        )

        print(f"Connection from {addr} closed")
        conn.close()

    def start(self):
        """
        Starts the IRC server
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self.host, self.port))
        sock.listen()

        while True:
            conn, addr = sock.accept()

            # add client to list of connected clients
            self.clients[addr] = {"conn": conn, "username": None}
            # start a new thread to handle the client
            threading.Thread(target=self.handle_client, args=(conn, addr)).start()


class Client:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def handle_recv(self, conn: socket.socket):
        while True:
            if conn.fileno() == -1:
                break

            data = conn.recv(1024)
            if not data:
                break

            data = json.loads(data.decode("utf-8"))
            time, username, message = data["time"], data["username"], data["message"]
            print("{} [ {:>12s} ] {}".format(time, username, message))

    def handle_send(self, conn: socket.socket):
        while True:
            if conn.fileno() == -1:
                break

            message = input()
            data = json.dumps({"message": message}).encode("utf-8")
            conn.send(data)

            if re.match("^/QUIT", message):
                break

    def start(self):
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((self.host, self.port))

        print(f"Client has been assigned socket name {conn.getsockname()}")

        threading.Thread(target=self.handle_recv, args=(conn,)).start()
        threading.Thread(target=self.handle_send, args=(conn,)).start()


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

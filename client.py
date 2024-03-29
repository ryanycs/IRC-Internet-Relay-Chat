import json
import re
import socket
import threading
import time


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

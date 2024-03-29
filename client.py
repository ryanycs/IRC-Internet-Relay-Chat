import json
import re
import socket
import threading


class Client:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def handle_recv(self, conn: socket.socket):
        """
        Handles receiving messages from the server
        """
        while True:
            # if the connection is closed, break the loop
            if conn.fileno() == -1:
                break

            data = conn.recv(1024)
            if not data:
                break

            data = json.loads(data.decode("utf-8"))
            time, username, message = (
                data.get("time", None),
                data.get("username", None),
                data.get("message", None),
            )
            print("{} [ {:>12s} ] {}".format(time, username, message))

    def handle_send(self, conn: socket.socket):
        """
        Handles sending messages to the server
        """
        while True:
            # if the connection is closed, break the loop
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

        # start two threads to handle sending and receiving data
        threading.Thread(target=self.handle_recv, args=(conn,)).start()
        threading.Thread(target=self.handle_send, args=(conn,)).start()

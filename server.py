import json
import re
import socket
import threading
import time


class User:
    def __init__(
        self,
        conn: socket.socket,
        addr: tuple,
        username: str,
    ):
        self.conn = conn
        self.username = username
        self.addr = addr

    def __str__(self):
        return f"{self.username}\t{self.addr}\t['#public']"

    def __repr__(self):
        return self.__str__()


class Server:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.users = []
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

    def command_user(self, user: User, message: str):
        """
        Extracts the username from the message and adds it to the list of clients
        """
        # extract username from message
        username = re.match("^\/USER\s*(.*)", message).group(1)
        # add user to list of users
        user.username = username
        # notify all connected clients that a new user has joined
        for client in self.users:
            self.send_message(
                client.conn,
                "-->",
                f"{user.username} has joined #public.",
            )

    def command_who(self, user: User, message: str):
        """
        Sends a list of all connected clients to the client
        """
        tmpstr = []
        for client in self.users:
            # only show clients that have set a username
            if client.username is not None:
                tmpstr.append(f"{client.username}\t{client.addr}\t['#public']")
        message = "USER\tFROM\tCHANNEL\n" + "\n".join(tmpstr)
        self.send_message(user.conn, None, message)

    def command_quit(self, user: User, message: str):
        """
        Closes the connection with the client
        """
        match_obj = re.match("/QUIT\s*(.*)", message)
        message = match_obj.group(1) if match_obj else None

        # notify all connected clients that a user has left
        for client in self.users:
            if client == user:
                continue
            if message:
                # send quit message
                self.send_message(client.conn, user.username, message)
            self.send_message(
                client.conn,
                "-->",
                f"{user.username} has left #public.",
            )

        user.conn.close()
        try:
            self.users.remove(user)
        except ValueError:
            pass

    def handle_client(self, user: User):
        """
        Handles a new client connection
        """
        print(f"New connection from {user.addr}")

        while True:
            # check if connection is still open
            if user.conn.fileno() == -1:
                break

            data = user.conn.recv(1024)
            if not data:
                break
            data = json.loads(data.decode("utf-8"))
            message = data["message"]
            print(f"from {user.addr}, msg = {message}")

            match_obj = re.match("/[A-Z]+", message)
            command = match_obj.group() if match_obj else None
            if command in self.commands.keys():
                # execute command
                self.commands[command](user, message)
            else:
                # check if user has set a username
                if user.username is None:
                    self.send_message(user.conn, "-->", "Please set a username first.")
                    continue
                # broadcast message to all connected clients
                for client in self.users:
                    if client != user:
                        self.send_message(
                            client.conn,
                            user.username,
                            message,
                        )

        print(f"Connection from {user.addr} closed")
        user.conn.close()

    def start(self):
        """
        Starts the IRC server
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self.host, self.port))
        sock.listen()
        print(f"Listening at {sock.getsockname()}")

        while True:
            try:
                conn, addr = sock.accept()

                # add client to list of connected clients
                user = User(conn, addr, None)
                self.users.append(user)

                # start a new thread to handle the client
                threading.Thread(target=self.handle_client, args=(user,)).start()
            except KeyboardInterrupt:
                break

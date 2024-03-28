## Introduction

In this exercise, we are going to implement a simplified IRC server/client. For more technical details, please refer to RFC 1459.

### Client

- The design of the client is very simple. Just implement two threads - one for sending and one for receiving.
### Server

- By default, an IRC server listens at tcp port 6667.
- After a client establishes a connection with the server, a thread was started to handle the send/recv of that socket in the background. The server keeps on waiting for a new client to connect.
- There are two types of messages from the clients. If it is a normal message, that will be forwarded to all other clients. If it starts with a slash ('/'), this is a so-called "slash command", which will trigger the server to perform some pre-defined tasks.
    - `/USER <username>` will specify a username of the connecting client.
    - `/WHO` will return a list of users logged into the server.
    - `/QUIT [<msg>]` will end a client session. The server will close the socket to this client.

## Usage

### Server
```bash
python3 main.py server [host] -p [port]
```

### Client
```bash
python3 main.py client [host] -p [port]
```
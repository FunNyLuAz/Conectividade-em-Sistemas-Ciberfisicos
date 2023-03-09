from socket_dns.server import server

import socket

MyServer = server(("127.0.0.1", 6969), socket.AF_INET, socket.SOCK_STREAM)
MyServer.start()
MyServer.awaitRunning()

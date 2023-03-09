from socket_dns.client import client

import socket

MyClient = client(socket.AF_INET, socket.SOCK_STREAM)
MyClient.connect(("127.0.0.1", 6969))

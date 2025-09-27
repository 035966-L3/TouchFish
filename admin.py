# now just test

import socket
s = socket.socket()
s.connect(('127.0.0.1', 11451))
while True:
    print(s.recv(1024).decode('utf-8'))
import socket

JETSON_IP = "192.168.1.126"
TCP_PORT = 8888
BUFFER_SIZE = 2048

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((JETSON_IP, TCP_PORT))
s.listen(1)

conn, addr = s.accept()
print "Connection addr: ", addr

print "Current position: "
while True:
	data = conn.recv(BUFFER_SIZE)
	if not data: break
	print "{0}\r".format(data),
	conn.send(data)

conn.close()

import socket
import threading, thread

JETSON_IP = "192.168.1.126"
TCP_PORT = 8888
BUFFER_SIZE = 2048

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((JETSON_IP, TCP_PORT))
s.listen(1)

print_lock = threading.Lock()

def sock_thread(c):
	while True:
		data = c.recv(BUFFER_SIZE)
		if not data:
			break

		print data
		print_lock.release()
		

edison, addr = s.accept()
print "Connection addr: ", addr

available_sensors = edison.recv(BUFFER_SIZE).split(" ")
print "Available sensors: ",
for sensor in available_sensors:
	print sensor + ",",
print

while True:
	print_lock.acquire()
	thread.start_new_thread(sock_thread, (edison,))
	cmd = raw_input("cmd >> ")
	#data = edison.recv(BUFFER_SIZE)
	#if not data: break
	#print "{0}\r".format(data),
	edison.send(cmd)
	if cmd == "exit":
		break

edison.close()

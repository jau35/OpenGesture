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
		
		if data[:4] == "!err":
			print data
			thread.interrupt_main()
			break
		else:
			print data
			print_lock.release()
		

edison, addr = s.accept()
print "[SERVER] Client %s has connected, addr: %s" % (edison, addr)

available_sensors = edison.recv(BUFFER_SIZE).split(" ")
print "Available sensors: ",
for sensor in available_sensors:
	print sensor + ",",
print

while True:
	try:
		print_lock.acquire()
		thread.start_new_thread(sock_thread, (edison,))
		cmd = raw_input("cmd >> ")
		edison.send(cmd)
		if cmd in ["exit", "q", "quit"]:
			break
	except KeyBoardInterrupt as e:
		print "error: exiting..."
		thread.exit()
		edison.close()

edison.close()

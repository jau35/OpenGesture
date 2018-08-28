import socket
import time
import mraa
import signal

JETSON_IP = "192.168.1.126"
TCP_PORT = 8888
BUFFER_SIZE = 1024
ROT_PIN = 1

if __name__ == '__main__':
    rot_encoder = mraa.Aio(ROT_PIN)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((JETSON_IP, TCP_PORT))

    while True:
        current_pos = rot_encoder.readFloat()
        message = "{:.4f}\r".format(current_pos)
        s.send(message)
        
    data = s.recv(BUFFER_SIZE)
    s.close()
    print "received data: ", data

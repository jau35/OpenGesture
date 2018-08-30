# some config stuff for server/client

SERVER_IP = "192.168.1.126"
TCP_PORT = 8888
BUFFER_SIZE = 1024

def clamp(n, lower, upper):

    return min(max(float(n), float(lower)), float(upper))

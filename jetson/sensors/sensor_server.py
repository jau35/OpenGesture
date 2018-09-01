#!/usr/bin/python
#	sensor_server.py: Server-side program to run Jetson TX2 dev board
#				Creates a binded host socket with IP in config.py
#				Handles multiple clients with socket mux select	
#				Currently receives commands from stdin and sends to all clients
#				

import socket
import sys
import select

from config import *

MAX_CLIENTS = 5

client_dict = {}


def start_server(host, port, num_clients):
	"""
	start_server: Creates TCP server socket for clients to connect to.
	Non-blocking socket is binded to given IP address and port.

	@param host: (str) IPv4 address of local host that will run server
	@param port: (int) TCP port number, should not conflict with known ports
	@param num_clients: (int) maximum number of clients the server will listen for
	@return sock: (socket obj) created server socket bound to host, port in
				non-blocking mode

	Example usage: start_server("192.168.1.2", 8000, 10)
	"""
	print "[SERVER] Starting server w/ IP: %s, port: %s" % (host, port)
	print "[SERVER] Max # clients supported: %d" % (num_clients)
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.setblocking(False)
	sock.bind((host, port))
	sock.listen(num_clients)

	return sock


def close_server(host_sock, client_list):
	"""
	close_server: Handles graceful shutdown of server and client sockets
	Traverses through connected clients and closes respective socket.

	@param host_sock: (socket obj) server's main binded socket
	@param client_list: (list) list of client socket objects created
						when first connected

	"""
	print "[SERVER] Server %s shutting down..." % (SERVER_IP) ,
	clients = [c for c in client_list if (c != host_sock) and (c != sys.stdin)]
	for client in clients:
		client.send("quit")
		client.close()

	host_sock.close()

	print "done\n"


def connect_client(sock):
	"""
	connect_client: Creates new TCP socket for client connections.
	A client will connect to the host socket created in start_server(), with
	the host socket accepting the new connection in non-blocking mode
	This function is called when the server detects (select) data is at the main
	host socket.

	@param sock: (socket obj) host/server TCP socket object
	@return conn: (socket obj) new client TCP socket object
	@return addr: (tuple) 2-tuple with IP and address of new client

	Example usage: connect_client(start_server("192.168.1.2", 8000, 10))

	"""
	conn, addr = sock.accept()
	print "[SERVER] Client %s has connected, addr: %s" % (conn, addr)
	available_sensors = conn.recv(BUFFER_SIZE).split(" ")
	print "[CLIENT %s] Available sensors: " % (addr[0]) ,
	for sensor in available_sensors:
		print sensor + ",",
	print
	
	conn.setblocking(False)

	return conn, addr



def main():
	host_sock = start_server(SERVER_IP, TCP_PORT, MAX_CLIENTS)
	read_socks = [host_sock, sys.stdin]

	server_on = True
	while server_on:	
		read_rdy, write_rdy, err_rdy = select.select(read_socks, [], [])
		
		for s in read_rdy:
			if s is host_sock:
				new_conn, new_addr = connect_client(host_sock)
				client_dict[new_conn] = new_addr
				read_socks.append(new_conn)

			elif s is sys.stdin:
				cmd = raw_input()
				print "sending data to %d client(s)" % (len(client_dict.keys()))
				for client in client_dict.keys():
					client.send(cmd)
				if cmd in ["exit", "q", "quit"]:
					server_on = False
					break
			else:
				data = s.recv(BUFFER_SIZE)
				if data:
					print "[CLIENT %s] %s" % (s.getsockname()[0], data)
	
	close_server(host_sock, read_socks)


if __name__ == '__main__':
	main()

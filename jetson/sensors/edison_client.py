#!/usr/bin/python
#       sensor_client.py: client-side program to run on Intel Edison dev board
#               This program creates a TCP socket connection with SERVER_IP @ port TCP_PORT
#				New commands are received, parsed, and distributed within respective HW
#				Primary HW calls (mraa/upm) are defined in edison_sensors.py
#
#       Author: Dylan Wong
#
import socket
import signal
import sys
from config import *
from edison_sensors import *


# declaration for SIGINT signal handler error
class CloseError(Exception):
    pass


# prototype exception if an incorrect device is commanded
class InvalidDeviceError(Exception):
    pass


def sig_handler(sig, frame):
    """
    sig_handler: Signal handler used for SIGINT, raises the CloseError exception

    @param sig: (int) signal from kernel
    """
    raise CloseError("Received signal " + str(sig))


def parse_command(cmd):
    """
    parse_command: Takes input stream from socket stream and splits into commands + args
    Commands are sent from server (Jetson) to client (this process) to perform
    interfacing with sensors

    @param cmd: (str) raw string received form server in socket
    @return obj: (str) the name of the sensor object, i.e. blueLED
    @return action: (str) the action to perform on sensor object, i.e. ON/OFF
    @return opt: (str) add'l options or arguments for action, i.e. PWM value

    Example usage: parse_command("blueLED ON 45")
    """
    tok = cmd.split(" ")
    obj = tok[0]
    action = None
    opt = None

    if len(tok) == 2:
        action = tok[1]

    elif len(tok) > 2:
        action = tok[1]
        opt = tok[2:]


    return obj, action, opt


def exec_command(deviceList, obj, action, opt):
    """
    exec_command: Uses result of parse_command to perform respective I/O
    commands on obj. Explicitly looks for LEDs or sensors listed in deviceList
    Calls led_action if obj is an LED, or get_grove_value if obj is a sensor
    Checks if the original command also contains a exit/quit sequence

    @param deviceList: (dict) sensor name(key): sensor obj (value)
    @param obj: (str) the name of the sensor object, i.e. blueLED
    @param action: (str) the action to perform on sensor object, i.e. ON/OFF
    @param opt: (str) add'l options or arguments for action, i.e. PWM value
    @return ret_msg: (str) confirm msg if LED obj, or sensor read value

    Example usage: exec_command(deviceDictionary, "blueLED", "ON", "45")
    """
    if obj.lower() in ["exit", "q", "quit"]:
        print "[SERVER] Server %s shutting down..." % (SERVER_IP)
        return None

    if obj not in deviceList.keys():
        print "invalid cmd device"
        return None

    print obj, action, opt
    
    # list comprehension, parses for read-only sensors
    sensors_only = [s for s in deviceList if (s[-3:] != "LED") and \
            (s != "lcd") and (s != "buzz")]

    # retrieves sensor obj from io_setup() in dictionary
    device_obj = deviceList[obj]

    # checks if main obj command is an LED
    if obj[-3:].lower() == "led":
        duty_cycle = None

        if action.lower() == "on" :
            state = 1

            # no PWM val specified
            if opt is None:
                duty_cycle = 100

            else:
                # safety check, clips PWM val at min/max
                try:
                    duty_cycle = clamp(float(opt[0]), 0, 100)

                    if duty_cycle == 0:
                        state = 0


                except TypeError as e:
                    print "err: pwm opt val"
                    return
        
        # action=OFF or otherwise
        else:
            state = 0

        # execute HW call to control LED
        led_action(device_obj, state, duty_cycle)
        ret_msg = obj + " cmd succ"
        return ret_msg

    # read from sensor obj
    elif obj in sensors_only:       
        sensor_val = get_grove_value(device_obj)
        ret_msg = str("{}: {:.3f}".format(obj, sensor_val))
        lcd_action(deviceList["lcd"], "c", None)
        lcd_action(deviceList["lcd"], "w", ret_msg)
        return ret_msg

    elif obj == "lcd":
        lcd_action(device_obj, action, opt)
        ret_msg = "lcd msg recv'd"
        return ret_msg

    elif obj == "buzz":
        ret_msg = buzz_action(device_obj, action, opt)
        return ret_msg

    else:
        return "Error?"


def connect_server(host, port, device_dict):
    """
    connect_server: Client-side program to connect to host server socket
    The client (this program) connects to the specified host server socket
    and sends a list of available connected sensors

    @param host: (str) IPv4 address of target server device
    @param port: (int) TCP port number, should be known between server-clients
    @param device_dict: (dict) dictionary of I/O devices created in
                    edison_sensors.py
    @return sock: (sock obj) created client socket to server, enables send/recv

    Example usage: connect_server("192.168.1.2", 8000, {"blueLED": blue_led}
    """
    try:
        # create and connect to TCP socket host
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))

    except socket.error:
        print "[CLIENT] Error connecting to server, is the server up?"
        sys.exit()

    print "Connection to server established: %s, %s" % (host, port)

    # sends device list to server to tell user what devices can be commanded
    sock.send(" ".join(device_dict.keys()))

    return sock



def close_client(sock_conn, display):
    """
    close_client: Called on shutdown of client program, allows for graceful
    shutdown and disconnect from socket, also turns off LCD

    @param sock_conn: (socket) socket connection object from socket.socket call
    @param display: (LCD obj) LCD display variable to clear, turn off, etc

    Example usage: close_client(sock, lcd)
    """
    print "Closing client...",
    data = sock_conn.recv(BUFFER_SIZE)
    sock_conn.close()

    display.clear()
    display.backlightOff()
    display.displayOff()
    print "done\n"



if __name__ == '__main__':
    # SIGINT handler
    signal.signal(signal.SIGINT, sig_handler)


   # primary device list dictionary
    devices = io_setup()

    sock = connect_server(SERVER_IP, TCP_PORT, devices)

    while True:
        data = sock.recv(BUFFER_SIZE)
        
        if not data:
            break
        
        else:
            print "command recv'd: ", data
            
            try:
                # "blueLED" "ON" 45
                entity, action, option = parse_command(data)

                if entity not in devices.keys():
                    raise InvalidDeviceError

                client_ret = exec_command(devices, entity, action, option)

                if client_ret is None:
                    raise CloseError

                else:
                    sock.send(client_ret)

            except CloseError:
                close_client(sock, devices["lcd"])
                sys.exit()

            except InvalidDeviceError:
                sock.send("!err: invalid device command")
                continue


    close_client(sock, devices["lcd"])


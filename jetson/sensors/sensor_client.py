#!/usr/bin/python
#       sensor_client.py: client-side program to run on Intel Edison dev board
#               Additional sensors are connected to the Grove breakout shield
#               LEDs and sensors are interfaced with using mraa and upm libraries
#               This program creates a TCP socket connection with JETSON_IP @ port TCP_PORT
#
#       Author: Dylan Wong
#
import socket
import time
import mraa
import signal
from upm import pyupm_grove as grove
from upm import pyupm_jhd1313m1 as groveLCD

JETSON_IP = "192.168.1.126"
TCP_PORT = 8888
BUFFER_SIZE = 1024
ROT_PIN = 1
SOUND_PIN = 2
TEMP_PIN = 3
LIGHT_PIN = 0

RED_PIN = 6
GREEN_PIN = 3
BLUE_PIN = 5
PWM_PINS = [3, 5, 6, 9, 10, 11]
PWM_PER = 500

# declaration for SIGINT signal handler error
class CloseError(Exception):
    pass


def sig_handler(sig, frame):
    """
    sig_handler: Signal handler used for SIGINT, raises the CloseError exception

    @param sig: (int) signal from kernel
    """
    raise CloseError("Received signal " + str(sig))


def io_setup():
    """
    io_setup: I/O setup for GPIO and Grove sensors
    Red, Green, Blue LEDs are initialized with PWM pins, period = PWM_PER us
    Rotary encoder, sound, temperature, and light sensors
    JHD1313M1 I2C display driver

    Example usage: io_setup()
    """
    global red_led, green_led, blue_led
    global rotary_enc, sound_sensor, temp_sensor, light_sensor, lcd

    red_led = mraa.Pwm(RED_PIN)
    green_led = mraa.Pwm(GREEN_PIN)
    blue_led = mraa.Pwm(BLUE_PIN)

    # PWM_PER = 500 us == 2 kHz freq.
    red_led.period_us(PWM_PER)
    green_led.period_us(PWM_PER)
    blue_led.period_us(PWM_PER)

    # enable PWM and turn off LEDs
    red_led.enable(True)
    red_led.write(0)
    green_led.enable(True)
    green_led.write(0)
    blue_led.enable(True)
    blue_led.write(0)

    # I2C addresses: 0x3E (LCD_ADDRESS), 0x62 (RGB_ADDRESS)
    lcd = groveLCD.Jhd1313m1(0, 0x3E, 0x62)
    lcd.clear()
    lcd.backlightOn()
    lcd.setColor(0, 255, 230)

    rotary_enc = grove.GroveRotary(ROT_PIN)
    sound_sensor = mraa.Aio(SOUND_PIN)
    temp_sensor = grove.GroveTemp(TEMP_PIN)
    light_sensor = grove.GroveLight(LIGHT_PIN)


# takes input stream from SOCK_STREAM and parses commands + arguments
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
        print "exiting..."
        return None

    if obj not in deviceList.keys():
        print "invalid device"
        return

    print obj, action, opt
    
    # list comprehension, parses for read-only sensors
    sensors_only = [s for s in deviceList if (s[-3:] != "LED") and (s != "lcd")]

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

                    # safety checks, clips PWM val at min/max
            elif float(opt) < 0:
                duty_cycle = 0
                state = 0

            elif float(opt) > 100:
                duty_cycle = 100

            else:
                duty_cycle = float(opt)

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

    else:
        return "Error?"


def led_action(led, state, pwm=None):
    """
    led_action: Calls PWM write to LED pin with duty cycle (0.0f to 1.0f)

    @param led: (mraa.Pwm) PWM object from device list
    @param state: (int) determines whether LED will be turned OFF or ON
    @param pwm: (float) defaults None, PWM duty cycle (0% - 100%)
            to drive LED pin

    Example usage: led_action(blueLED, state=1, 45)
    """
    if pwm and state:
        led.write(pwm / 100.0)
    elif state == 0:
        led.write(0)

    return


def get_grove_value(sensor):
    """
    get_grove_value: Reads from sensor with upm lib and converts to human-
    readable unit; rotary_enc=degrees, temp=Fahrenheit, light=lux

    @param sensor: (Grove obj) sensor object from device list
    @return sensor_read: (float) corresponding converted sensor reading

    Example usage: get_grove_value(light_sensor)
    """
    sensor_read = None

    # rotary encoder, absolute pos in degrees
    if sensor == rotary_enc:
        abs_pos = sensor.abs_value()
        deg_pos = sensor.abs_deg()

        sensor_read = float(deg_pos)

    # temp sensor, returns ambient temperature in Fahrenheit
    elif sensor == temp_sensor:
        temp_cels = sensor.value()
        temp_fahr = temp_cels * 9.0/5.0 + 32

        sensor_read = float(temp_fahr)

    # light sensor, gets raw val and approximated lux val
    elif sensor == light_sensor:
        light_raw = sensor.raw_value()
        light_lux = sensor.value()

        sensor_read = float(light_lux)

    return sensor_read


def lcd_action(display, cmd, msg):
    """
    lcd_action: Performs various LCD functions (write, setColor, clear, etc)

    @param display: (LCD obj) LCD variable from upm
    @param cmd: (str) determines the JHD1313M1 class function to be called
    @param msg: (str) string message or RGB values to setColor

    Example usage: lcd_action(lcd, "write", "hello world!")
   """

    # lcd write, clears and setCursor(0,0)
    if cmd.lower() in ["w", "write", "wr"]:
        display.clear()
        display.home()
        str_msg = msg

        # in the case that lcd w is called from server
        # server drives this function with msg as a list of strings
        if type(msg) is list:
            str_msg = " ".join(msg)

        # mitigates display runoff, moves cursor to next line if exceeds 
        # 16 char width
        if len(str_msg) > 16:
            display.write(str_msg[:16])
            display.setCursor(1,0)
            display.write(str_msg[16:])

        else:
            display.write(str_msg)

    elif cmd.lower() in ["c", "clear", "clc"]:
        display.clear()
        display.home()

    # display.setColor(R, G, B), 0d - 255d
    elif cmd.lower() in ["color", "colo", "setcolor"]:
        display.setColor(int(msg[0]), int(msg[1]), int(msg[2]))
    
    else:
        print "lcd_action err"

    return


def close_client(sock_conn, display):
    """
    close_client: Called on shutdown of client program, allows for graceful
    shutdown and disconnect from socket, also turns off LCD

    @param sock_conn: (socket) socket connection object from socket.socket call
    @param display: (LCD obj) LCD display variable to clear, turn off, etc

    """
    print "Closing client...",
    data = sock_conn.recv(BUFFER_SIZE)
    sock_conn.close()

    display.clear()
    display.backlightOff()
    display.displayOff()
    print "done\n"


if __name__ == '__main__':
    signal.signal(signal.SIGINT, sig_handler)

    global red_led, green_led, blue_led
    global rotary_enc, sound_sensor, temp_sensor, light_sensor, lcd

    io_setup()
    # primary device list dictionary
    devices = { "redLED": red_led, \
            "greenLED": green_led, \
            "blueLED": blue_led, \
            "rot": rotary_enc, \
            "sound": sound_sensor, \
            "temp": temp_sensor, \
            "light": light_sensor, \
            "lcd": lcd \
            }

    # create and connect to TCP socket host
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((JETSON_IP, TCP_PORT))

    print "Connection to server established: %s, %s" % (JETSON_IP, TCP_PORT)

    # sends device list to server to tell user what devices can be commanded
    s.send(" ".join(devices.keys()))

    try:
        while True:
            data = s.recv(BUFFER_SIZE)
            if not data:
                break
            else:
                print "command recv'd: ", data
                entity, action, option = parse_command(data)

                if entity not in devices.keys():
                    s.send("!err: invalid device")
                    print "!err: something?"
                    break

                client_ret = exec_command(devices, entity, action, option)

                if client_ret is None:
                    break
                else:
                    s.send(client_ret)

    except CloseError as close_err:
        close_client(s, lcd)

    close_client(s, lcd)


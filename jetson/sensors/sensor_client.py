import socket
import time
import mraa
import signal
from upm import pyupm_grove as grove

JETSON_IP = "192.168.1.126"
TCP_PORT = 8888
BUFFER_SIZE = 1024

ROT_PIN = 1
SOUND_PIN = 2
TEMP_PIN = 3
LIGHT_PIN = 0

RED_PIN = 6
BLUE_PIN = 5
GREEN_PIN = 3
PWM_PINS = [3, 5, 6, 9, 10, 11]
PWM_PER = 500


class CloseError(Exception):
    pass

def sig_handler(sig, frame):
    raise CloseError("Received signal " + str(sig))


def setup():
    global red_led, green_led, blue_led
    global rotary_enc, sound_sensor, temp_sensor, light_sensor

    red_led = mraa.Pwm(RED_PIN)
    blue_led = mraa.Pwm(BLUE_PIN)
    green_led = mraa.Pwm(GREEN_PIN)

    red_led.period_us(PWM_PER)
    blue_led.period_us(PWM_PER)
    green_led.period_us(PWM_PER)

    red_led.enable(True)
    red_led.write(0)
    blue_led.enable(True)
    blue_led.write(0)
    green_led.enable(True)
    green_led.write(0)

    rotary_enc = grove.GroveRotary(ROT_PIN)
    sound_sensor = mraa.Aio(SOUND_PIN)
    temp_sensor = grove.GroveTemp(TEMP_PIN)
    light_sensor = grove.GroveLight(LIGHT_PIN)

def parse_command(cmd):
    tok = cmd.split(" ")
    obj = tok[0]
    action = None
    opt = None

    if len(tok) == 2:
        action = tok[1]

    elif len(tok) == 3:
        action = tok[1]
        opt = tok[2]
    
    print obj, action, opt
    return obj, action, opt


def exec_command(deviceList, obj, action, opt):
    if obj not in deviceList.keys():
        print "invalid device"
        return

    print obj, action, opt

    if obj.lower() in ["exit", "q", "quit"]:
        print "exiting..."
        return None

    device_obj = deviceList[obj]
    if obj[-3:].lower() == "led":
        duty_cycle = None

        if action.lower() == "on" :
            state = 1

            if opt is None:
                duty_cycle = 100
            
            elif (0 < float(opt) < 100):
                duty_cycle = float(opt)


        else:
            state = 0

        led_action(device_obj, state, duty_cycle)
        ret = obj + " cmd succ"
        return ret

    else:
        sensor_val = get_grove_value(device_obj) 
        ret_msg = str("{:.3f}".format(sensor_val))
        return ret_msg

def led_action(led, cmd, pwm=None):
    if pwm and cmd:
        led.write(pwm/100.0)
    elif cmd == 0:
        led.write(0)

    return


def get_grove_value(sensor):
    sensor_read = None

    if sensor == rotary_enc:
        abs_pos = sensor.abs_value()
        deg_pos = sensor.abs_deg()
        
        sensor_read = float(deg_pos)

    elif sensor == temp_sensor:
        temp_cels = sensor.value()
        temp_fahr = temp_cels * 9.0/5.0 + 32

        sensor_read = float(temp_fahr)

    elif sensor == light_sensor:
        light_raw = sensor.raw_value()
        light_lux = sensor.value()

        sensor_read = float(light_lux)


    return sensor_read

if __name__ == '__main__':
    signal.signal(signal.SIGINT, sig_handler)
    
    global red_led, blue_led, green_led
    global rotary_enc, sound_sensor, temp_sensor, light_sensor
    
    setup()
    devices = { "redLED": red_led, \
            "blueLED": blue_led,\
            "greenLED": green_led,\
            "rot": rotary_enc,\
            "sound": sound_sensor,\
            "temp": temp_sensor,\
            "light": light_sensor\
            }


    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((JETSON_IP, TCP_PORT))

    print "Connection to server established: %s, %s" % (JETSON_IP, TCP_PORT)
    
    s.send(" ".join(devices.keys()))

    try:
        while True:
            data = s.recv(BUFFER_SIZE)
            if not data:
                break
            else:
                print "command recv'd: ", data
                entity, action, option = parse_command(data)
                client_ret = exec_command(devices, entity, action, option)
                
                if client_ret is None:
                    raise CloseError
                else:
                    s.send(client_ret)    

    except CloseError as close_err:    
        data = s.recv(BUFFER_SIZE)
        s.close()
        print "received data: ", data

#!/usr/bin/python
#       edison_sensors.py: Python APIs to interface with connected sensors on 
#               Intel Edison
#               Additional sensors are connected to the Grove breakout shield
#               LEDs and sensors are interfaced with using mraa and upm libraries
#
#       Author: Dylan Wong
#

import mraa
from upm import pyupm_grove as grove
from upm import pyupm_jhd1313m1 as groveLCD
from upm import pyupm_buzzer as groveBuzzer
from config import *


ROT_PIN = 1
SOUND_PIN = 2
TEMP_PIN = 3
LIGHT_PIN = 0

RED_PIN = 6
GREEN_PIN = 3
BLUE_PIN = 5
BUZZ_PIN = 9
PWM_PINS = [3, 5, 6, 9, 10, 11]
PWM_PER = 500


def io_setup():
    """
    io_setup: I/O setup for GPIO and Grove sensors
    Red, Green, Blue LEDs are initialized with PWM pins, period = PWM_PER us
    Rotary encoder, sound, temperature, and light sensors
    JHD1313M1 I2C display driver

    @return device_list: (list) list of all created mraa/upm objects
    Example usage: io_setup()
    """
    
    global red_led, green_led, blue_led
    global rotary_enc, sound_sensor, temp_sensor, light_sensor
    global lcd, buzzer

    devices = {}


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

    devices["redLED"] = red_led
    devices["greenLED"] = green_led
    devices["blueLED"] = blue_led

    # I2C addresses: 0x3E (LCD_ADDRESS), 0x62 (RGB_ADDRESS)
    lcd = groveLCD.Jhd1313m1(0, 0x3E, 0x62)
    lcd.clear()
    lcd.backlightOn()
    lcd.setColor(255, 255, 255)
    devices["lcd"] = lcd

    rotary_enc = grove.GroveRotary(ROT_PIN)
    sound_sensor = mraa.Aio(SOUND_PIN)
    temp_sensor = grove.GroveTemp(TEMP_PIN)
    light_sensor = grove.GroveLight(LIGHT_PIN)

    devices["rot"] = rotary_enc
    devices["sound"] = sound_sensor
    devices["temp"] = temp_sensor
    devices["light"] = light_sensor

    buzzer = groveBuzzer.Buzzer(BUZZ_PIN)
    buzzer.stopSound()
    buzzer.setVolume(0.125)
    devices["buzz"] = buzzer

    return devices


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

    global red_led, green_led, blue_led
    global rotary_enc, sound_sensor, temp_sensor, light_sensor
    global lcd, buzzer

    sensor_read = None

    # rotary encoder, absolute pos in degrees
    if sensor == rotary_enc:
        abs_pos = sensor.abs_value()
        deg_pos = sensor.abs_deg()

        sensor_read = float(deg_pos)

    # temp sensor, returns ambient temperature in Fahrenheit
    elif sensor == temp_sensor:
        # reads temp twice to allow for correct NTC read
        temp_cels = sensor.value()
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
    @param msg: (list) list of strings, gets parsed up into messages and colors

    Example usage: lcd_action(lcd, "write", "hello world!")
    """

    # lcd write, clears and setCursor(0,0)
    if cmd.lower() in ["w", "write", "wr"]:
        display.clear()
        display.home()
        str_msg = msg

        if not msg:
            return

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
        R = clamp(int(msg[0]), 0, 255)
        G = clamp(int(msg[1]), 0, 255)
        B = clamp(int(msg[2]), 0, 255)
        display.setColor(R, G, B)
    
    else:
        print "lcd_action err"

    return


def buzz_action(buzz, cmd, val):
    """
    buzz_action: Interfaces with upm_buzzer API (playSound, setVolume, etc)

    @param buzz: (buzzer obj) buzzer variable from upm
    @param cmd: (str) determines whether setVolume, getVolume, or playSound
    @param val: (list) list of strings for sound tone, duration, or volume
    @return buzz_ret (str) confirmation message sent back to server
    """
    chords = {"do":groveBuzzer.BUZZER_DO, "re":groveBuzzer.BUZZER_RE, \
            "mi": groveBuzzer.BUZZER_MI, "fa": groveBuzzer.BUZZER_FA, \
            "sol": groveBuzzer.BUZZER_SOL, "la": groveBuzzer.BUZZER_LA, \
            "si": groveBuzzer.BUZZER_SI};

    buzz_ret = None

    if cmd.lower() in ["sv", "setvol", "setvolume"]:
        vol_set = clamp(float(val[0]), 0.0, 1.0)
        buzz.setVolume(vol_set)
        buzz_ret = "buzzer volume set to %0.3f" % (vol_set)

    elif cmd.lower() in ["gv", "getvol", "getvolume"]:
        buzz_ret = str(buzz.getVolume())

    elif cmd.lower() in ["p", "play"]:
        sound = val[0]
        duration_us = int(val[1])

        freq = 0
        try:
            freq = int(sound)

        except ValueError:
            if sound.lower() in chords.keys():
                freq = chords[sound]
			
			else:
				buzz_ret = "buzz: invalid tone"
				return buzz_ret
    
        buzz_ret = "buzz played %s for %d us" % (sound, duration_us)
        buzz.playSound(freq, duration_us)

    else:
        print "buzz_action err"

    return buzz_ret



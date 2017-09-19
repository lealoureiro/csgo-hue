#!/usr/local/bin/python3.5

import logging
import time
import threading
from phue import Bridge
from bottle import run, request, HTTPResponse, Bottle
from rgbxy import Converter
from rgbxy import GamutC


logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

logger.addHandler(ch)


app = Bottle()


converter = Converter(GamutC)
red_xy = converter.rgb_to_xy(255, 0, 0)
red = {'transitiontime': 0, 'xy': red_xy}
green = {'transitiontime': 0, 'xy': converter.rgb_to_xy(0, 255, 0)}
blue = {'transitiontime': 0, 'xy': converter.rgb_to_xy(0, 0, 255)}
orange = {'transitiontime': 0, 'xy': converter.rgb_to_xy(255, 165, 0)}
yellow = {'transitiontime': 0, 'xy': converter.rgb_to_xy(255, 255, 0)}


bridge = Bridge('192.168.178.38')

bomb_planted = False

def set_bomb_alarm_on():
    global bomb_planted
    if not bomb_planted:
        bridge.set_light('Portable', red)
        bomb_planted = True
        t = threading.Thread(target=blink_red)
        t.start()

def set_bomb_alarm_off():
    global bomb_planted
    if bomb_planted:
        bomb_planted = False
        bridge.set_light('Portable', {'on': True, 'bri': 255})

@app.post('/')
def handle_event():
    logger.debug(request.json)

    if 'round' in request.json:
       process_round(request.json['round'])

def process_round(round):
    if 'bomb' in round:
        process_bomb_state(round['bomb'])
    else:
        process_round_state(round['phase'])

def process_bomb_state(bomb_state):
    if bomb_state == 'planted':
        set_bomb_alarm_on()
    elif bomb_state == 'defused':
        set_bomb_alarm_off()
        bridge.set_light('Portable', blue)
    elif bomb_state == 'exploded':
        set_bomb_alarm_off()
        bridge.set_light('Portable', orange)

    logger.info('Bomb: %s', bomb_state)

def process_round_state(round_state):
    if round_state == 'live':
        set_bomb_alarm_off()
        bridge.set_light('Portable', green)
    elif round_state == 'freezetime':
        set_bomb_alarm_off()
        bridge.set_light('Portable', yellow)

    logger.info('Round: %s',round_state)


def blink_red():
    logger.info('Blinking red light')
    light_state = False
    while bomb_planted:
        logger.info('Setting red light %s', light_state)
        blink_command = {'xy': red_xy, 'on': light_state}
        bridge.set_light('Portable', blink_command)
        light_state = not light_state
        time.sleep(0.5)

def main():

    logger.info("Starting Application")

    logger.info("Initializing Hue Brigde")
    bridge.connect()

    bridge.set_light('Portable', 'bri', 255)

    logger.info("Starting endpoint")
    run(app, host='localhost', port=3000, debug=True)


if __name__ == "__main__":
    main()


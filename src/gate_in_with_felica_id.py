#!/usr/bin/env python
# -*- coding: utf-8 -*-
 
import binascii
import nfc
import time
import re
import commands
import urllib
import urllib2
import time
import RPi.GPIO as GPIO

id_pattern = re.compile('ID=([0-9a-z]+)')

led_r_pin   = 14
led_g_pin = 15
led_b_pin  = 18

GPIO.setmode(GPIO.BCM)
GPIO.setup(led_r_pin, GPIO.OUT)
GPIO.setup(led_g_pin, GPIO.OUT)
GPIO.setup(led_b_pin, GPIO.OUT)

def led(r, g, b):
    GPIO.output(led_r_pin, not r)
    GPIO.output(led_g_pin, not g)
    GPIO.output(led_b_pin, not b)

def post(id):
    url = "https://halake-users.herokuapp.com/api/v1/nfc_ids"
    params = urllib.urlencode({"nfc_id": id})
    req = urllib2.Request(url)
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    req.add_data(params)
    res = urllib2.urlopen(req).read()
    print "response: " + res
    return res

def performe(tag):
    tag_str = str(tag)
    matched = id_pattern.search(tag_str)
    if matched:
        id = matched.group(1)
        print "id: " + id
        res =  post(id)
        if res == 'no-user':
            led(True, False, False)
        else:
            led(False, False, True)
    time.sleep(2)
    led(False, False, False)

def connected(tag):
    try:
        performe(tag)
    except Exception as e:
        print e

led(False, False, False)
clf = nfc.ContactlessFrontend('usb')
while True:
    clf.connect(rdwr={'on-connect': connected})
    time.sleep(0.1)

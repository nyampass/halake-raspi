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

id_pattern = re.compile('ID=([0-9a-z]+)')

commands.getoutput("sudo gpio-admin export 14")
commands.getoutput("echo out > /sys/class/gpio/gpio14/direction")

commands.getoutput("sudo gpio-admin export 15")
commands.getoutput("echo out > /sys/class/gpio/gpio15/direction")

def led(r, g, b):
    cmd = "echo " + str(0 if r else 1) + " > /sys/class/gpio/gpio15/value"
    commands.getoutput(cmd)
    cmd = "echo " + str(0 if b else 1) + " > /sys/class/gpio/gpio14/value"
    commands.getoutput(cmd)

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

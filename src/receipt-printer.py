#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import RPi.GPIO as GPIO
import json
import os
import re
import time
from connpass import Connpass
from datetime import datetime
from escpos.constants import FS, ESC
from escpos.printer import Usb
from escpos.exceptions import USBNotFoundError

image_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.dirname(image_dir)

def set_sjis_mode(p):
    p._raw(FS + b'C\x01')  # set SJIS mode


def set_quadruple_size_mode(p):
    p._raw(FS + b'W\x01')


def unset_quadruple_size_mode(p):
    p._raw(FS + b'W\x00')


def text_sjis(p, text):
    p._raw(text.encode('Shift_JIS'))


def print_receipt(p, dt, records):
    set_sjis_mode(p)
    p.set(align='right', smooth=True)
    text_sjis(p, dt.strftime('%Y/%m/%d %H:%M\n'))
    p.set(align='center', smooth=True)
    p.image(image_dir + '/halake-logo.png')
    set_quadruple_size_mode(p)
    text_sjis(p, '\n領収書\n\n\n')
    p.set(align='center', smooth=True, text_type='U')
    text_sjis(p, '                          様\n\n\n')
    if len(records) == 0:
        text_sjis(p, '                      円\n\n\n')
        unset_quadruple_size_mode(p)
        text_sjis(p, '                        として\n')
    else:
        unset_quadruple_size_mode(p)
        sum = 0
        for record in records:
            sum += record['price']
            p.set(align='left', smooth=True)
            text_sjis(p, record['title'] + '\n')
            p.set(align='right', smooth=True)
            text_sjis(p, '￥' + str(record['price']) + '\n')
        set_quadruple_size_mode(p)
        p.set(align='center', smooth=True, text_type='B', height=2, width=2)
        text_sjis(p, '\n合計  ￥' + str(sum) + '\n')
        unset_quadruple_size_mode(p)
    p.set(align='right', smooth=True)
    text_sjis(p, '\n\n〒343-0827 埼玉県越谷市レイクタウン8-11-1\n')
    text_sjis(p, 'レイクタウンオークラビル4F\n\n')
    p.set(align='center', smooth=True)
    set_quadruple_size_mode(p)
    text_sjis(p, 'ニャンパス株式会社\n')
    unset_quadruple_size_mode(p)
    p.set(align='right', smooth=True)
    text_sjis(p, '\nURL:http://nyampass.com TEL:050-3159-6010\n')
    p.cut()


CONNPASS_GROUP_ID = 1382


def event_headeline(event, start_at):
    title = event['title']

    title = re.sub(r'^【\d+/\d+開催】', '',
                   re.sub(r'^【\d+/\d+】', '', title))

    return '・{month}/{day} {title} ({accepted}/{limit}名)'.format(
        title=title,
        month=start_at.month,
        day=start_at.day,
        limit=event['limit'],
        accepted=event['accepted'])


# Load .secret data
with open(root_dir + '/.secret.json') as f:
    secret = json.load(f)


def receipt_info():
    header = """HaLake Wifi
SSID: halake-a, halake-a2
パスワード: {password}

今後のイベント情報:
http://halake.connpass.com/

""".format(**secret)

    events = []
    for event in Connpass().search(series_id=[CONNPASS_GROUP_ID])['events']:
        start_at = datetime.strptime(
            event['started_at'].split('T')[0], '%Y-%m-%d')
        if start_at > datetime.now():
            events.append({
                'date': start_at,
                'headline': event_headeline(event, start_at)
            })

    events = sorted(events, key=lambda event: event['date'])
    return header + '\n'.join([event['headline'] for event in events])


def print_info(p):
    set_sjis_mode(p)
    p.set(align='center', smooth=True)
    p.image(image_dir + '/halake-logo.png')
    p.set(align='left', smooth=True)
    text_sjis(p, receipt_info())
    p.cut()


def button_process(pin, action):
    def process():
        i = 0
        flag = False
        while True:
            if GPIO.input(pin):
                # print(pin, 'high')
                i = 0
                flag = False
            else:
                # print(pin, 'low')
                i += 1
                if i >= 5:
                    if not flag:
                        print(pin, "do action")
                        action()
                    flag = True
            yield
    return process()


def open_printer(vendor_id, product_id):
    try:
        return Usb(vendor_id, product_id, 0)
    except USBNotFoundError:
        print("cannot open printer")
        return None


PRINT_BUTTON = 22
DAY_BUTTON = 17
TWO_HOURS_BUTTON = 27
RESET_BUTTON = 18
INFO_BUTTON = 24
day_record = {'title': 'コワーキングスペース一日利用', 'price': 1000}
two_hours_record = {'title': 'コワーキングスペース2時間利用', 'price':  500}
vendor_id = 0x04b8
product_id = 0x0202

GPIO.setmode(GPIO.BCM)

GPIO.setup(PRINT_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DAY_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(TWO_HOURS_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(RESET_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(INFO_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)

records = []


def print_action():
    global records
    p = open_printer(vendor_id, product_id)
    if (p != None):
        print_receipt(p, datetime.now(), records)
        records = []
        p.close()


def reset_action():
    global records
    records = []


def info_action():
    p = open_printer(vendor_id, product_id)
    if (p != None):
        print_info(p)
        records = []
        p.close()

button_processes = []
button_processes.append(button_process(PRINT_BUTTON, print_action))
button_processes.append(button_process(
    DAY_BUTTON, lambda: records.append(day_record)))
button_processes.append(button_process(
    TWO_HOURS_BUTTON, lambda: records.append(two_hours_record)))
button_processes.append(button_process(RESET_BUTTON, reset_action))
button_processes.append(button_process(INFO_BUTTON, info_action))

print('start')
while True:
    for process in button_processes:
        next(process)
    time.sleep(0.01)

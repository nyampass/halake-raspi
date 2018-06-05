#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import RPi.GPIO as GPIO
import json
import os
import re
import time
from connpass import Connpass
from datetime import datetime, timedelta
from escpos.constants import FS, ESC
from escpos.printer import Usb
from escpos.exceptions import USBNotFoundError
from requests.exceptions import ConnectionError

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
    limit = event['limit']
    accepted = event['accepted']
    accepted_str = ''
    if limit == None:
        accepted_str = '({accepted}名)'.format(accepted=accepted)
    else:
        accepted_str = '({accepted}/{limit}名)'.format(accepted=accepted, limit=limit)

    return '・{month}/{day} {title} {accepted_str}'.format(
        title=title,
        month=start_at.month,
        day=start_at.day,
        accepted_str=accepted_str)


# Load .secret data
with open(root_dir + '/.secret.json') as f:
    secret = json.load(f)


events = []
got_event_at = None
CHECK_EVENT_INTERVAL = timedelta(hours = 1)


def get_events():
    global events
    new_events = []
    try:
        for event in Connpass().search(series_id=[CONNPASS_GROUP_ID])['events']:
            start_at = datetime.strptime(
                event['started_at'].split('T')[0], '%Y-%m-%d')
            if start_at > datetime.now():
                new_events.append({
                    'date': start_at,
                    'headline': event_headeline(event, start_at)
                })
        events = sorted(new_events, key=lambda event: event['date'])
    except ConnectionError as e:
        print("Cannot get events")
        print(e)


def check_events():
    global got_event_at
    if got_event_at == None or got_event_at < datetime.now() - CHECK_EVENT_INTERVAL:
        got_event_at = datetime.now()
        get_events()


def receipt_info():
    header = """HaLake Wifi
SSID: halake-a, halake-a2
パスワード: {password}

今後のイベント情報:
https://halake.connpass.com/

""".format(**secret)

    global events
    return header + '\n'.join([event['headline'] for event in events])


def print_info(p):
    set_sjis_mode(p)
    p.set(align='center', smooth=True)
    p.image(image_dir + '/halake-logo.png')
    p.set(align='left', smooth=True)
    text_sjis(p, receipt_info())
    p.cut()


def questions_receipt():
    return """よろしければアンケートにご協力ください

HaLakeをどのように知りましたか？
[ ] web検索
[ ] 友人からの紹介
[ ] 情報誌
[ ] その他(                              )

HaLakeをご利用になり、気になったことがありましたら、お知らせください。
気になったこと
(



                                         )

HaLakeまたご利用されたいですか？
[ ] 積極的に利用したい
[ ] たまに利用したい
[ ] 利用するかもしれない
[ ] あまり利用したくない
[ ] もう利用したくない、二度と

ご回答いただいたアンケートは入口付近の回収箱にお入れください。
ご協力ありがとうございました。"""


def print_questions(p):
    text_sjis(p, questions_receipt())
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

BUTTON_TOP_LEFT = 25
BUTTON_TOP_CENTER = 23
BUTTON_TOP_RIGHT = 18
BUTTON_BOTTOM_LEFT = 24
BUTTON_BOTTOM_CENTER = 22
BUTTON_BOTTOM_RIGHT = 17

PRINT_BUTTON = BUTTON_TOP_RIGHT
DAY_BUTTON = BUTTON_TOP_CENTER
TWO_HOURS_BUTTON = BUTTON_TOP_LEFT
RESET_BUTTON = BUTTON_BOTTOM_LEFT
INFO_BUTTON = BUTTON_BOTTOM_CENTER

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
        # print_questions(p)
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
    check_events()
    time.sleep(0.01)

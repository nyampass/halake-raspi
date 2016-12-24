#!/usr/bin/env python3

# -*- encoding: utf-8 -*-

import RPi.GPIO as GPIO
import time
from datetime import datetime
from escpos.printer import Usb
from escpos.constants import FS, ESC

def set_sjis_mode(p):
  p._raw(FS + b'C\x01') # set SJIS mode

def set_quadruple_size_mode(p):
  p._raw(FS + b'W\x01')

def unset_quadruple_size_mode(p):
  p._raw(FS + b'W\x00')

def text_sjis(p, text):
  p._raw(text.encode('Shift_JIS'))

def print_receipt(p, dt, records):
  set_sjis_mode(p)
  p.set(align = 'right', smooth = True)
  text_sjis(p, dt.strftime('%Y/%m/%d %H:%M\n'))
  p.set(align = 'center', smooth = True)
  p.image('halake-logo.png')
  set_quadruple_size_mode(p)
  text_sjis(p, '\n領収書\n\n\n')
  p.set(align = 'center', smooth = True, text_type = 'U')
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
      p.set(align = 'left', smooth = True)
      text_sjis(p, record['title'] + '\n')
      p.set(align = 'right', smooth = True)
      text_sjis(p, '￥' + str(record['price']) + '\n')
    set_quadruple_size_mode(p)
    p.set(align = 'center', smooth = True, text_type = 'B', height = 2, width = 2)
    text_sjis(p, '\n合計  ￥' + str(sum) + '\n')
    unset_quadruple_size_mode(p)
  p.set(align = 'right', smooth = True)
  text_sjis(p, '\n\n〒343-0827 埼玉県越谷市レイクタウン8-11-1\n')
  text_sjis(p, 'レイクタウンオークラビル4F\n\n')
  p.set(align = 'center', smooth = True)
  set_quadruple_size_mode(p)
  text_sjis(p, 'ニャンパス株式会社\n')
  unset_quadruple_size_mode(p)
  p.set(align = 'right', smooth = True)
  text_sjis(p, '\nURL:http://nyampass.com TEL:050-3159-6010\n')
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


PRINT_BUTTON = 22
DAY_BUTTON = 17
TWO_HOURS_BUTTON = 27
RESET_BUTTON = 18
day_record = {'title': 'コワーキングスペース一日利用' , 'price': 1000}
two_hours_record = {'title': 'コワーキングスペース2時間利用', 'price':  500}
p = Usb(0x04b8, 0x0202, 0)

GPIO.setmode(GPIO.BCM)

GPIO.setup(PRINT_BUTTON, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(DAY_BUTTON, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(TWO_HOURS_BUTTON, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(RESET_BUTTON, GPIO.IN, pull_up_down = GPIO.PUD_UP)

records = []

def print_action():
  global records
  print_receipt(p, datetime.now(), records)
  records = []

def reset_action():
  global records
  records = []

button_processes = []
button_processes.append(button_process(PRINT_BUTTON, print_action))
button_processes.append(button_process(DAY_BUTTON, lambda: records.append(day_record)))
button_processes.append(button_process(TWO_HOURS_BUTTON, lambda: records.append(two_hours_record)))
button_processes.append(button_process(RESET_BUTTON, reset_action))

print('start')
while True:
  for process in button_processes:
    next(process)
  time.sleep(0.01)

#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import json
import os
import re
import time
from connpass import Connpass
from datetime import datetime, timedelta
from escpos.constants import FS, ESC
from escpos.printer import Usb
from escpos.exceptions import USBNotFoundError
from json.decoder import JSONDecodeError
from requests.exceptions import ConnectionError
import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer


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

# Load .secret data
with open(root_dir + '/.secret.json') as f:
    secret = json.load(f)


events = []
got_event_at = None
CHECK_EVENT_INTERVAL = timedelta(hours = 1)

def receipt_info():
    header = """HaLake Wifi
SSID: halake
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


def open_printer(vendor_id, product_id):
    try:
        return Usb(vendor_id, product_id, 0)
    except USBNotFoundError:
        print("cannot open printer")
        return None

day_record = {'title': 'コワーキングスペース一日利用', 'price': 1000}
two_hours_record = {'title': 'コワーキングスペース2時間利用', 'price':  500}
vendor_id = 0x04b8
product_id = 0x0202

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
    global records
    p = open_printer(vendor_id, product_id)
    if (p != None):
        print_info(p)
        # print_questions(p)
        records = []
        p.close()

msg = ''

def total_print(request_json):
    global msg
    if 'items' not in request_json:
        if 'info' in request_json:
            info_action()
        elif request_json == r'{}':
            msg = 'Empty receipt'
            print_action()
        else:
            msg = 'Invalid content'
            return
    else:
        for record in request_json['items']:
            records.append(record)
        msg = 'Print receipt'
        print_action()

class MyHandler(BaseHTTPRequestHandler):
    global records
    global msg

    def do_POST(self):
        try:
            content_len = int(self.headers.get('content-length'))
            requestBody = json.loads(self.rfile.read(content_len).decode('utf-8'))

            total_print(requestBody)
            
            response = {'status' : 200,
                        'msg' : msg}
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            responseBody = json.dumps(response)

            self.wfile.write(responseBody.encode('utf-8'))

        except Exception as e:
            print("An error occured")
            print("The information of error is as following")
            print(type(e))
            print(e.args)
            print(e)
            response = { 'status' : 500,
                         'msg' : 'An error occured' }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            responseBody = json.dumps(response)

            self.wfile.write(responseBody.encode('utf-8'))

def run(server_class=HTTPServer, handler_class=MyHandler, server_name='', port=8008):

    server = server_class((server_name, port), handler_class)
    server.serve_forever()

def main():
    run(server_name='', port=8008)

print('start')

if __name__ == '__main__':
    main()
#!/bin/bash

#
# Install pip for python2 and python3
#
sudo apt-get install -y python-setuptools python-pip python3-setuptools python3-pip
sudo pip2 install --upgrade pip
sudo pip3 install --upgrade pip

#
# Install wiring-pi
#
sudo apt-get install -y python-dev
sudo pip2 install wiringpi2

#
# Install nfcpy
#
sudo pip2 install nfcpy

#
# Install python3 and python-escpos
#
sudo apt-get install -y python3-RPi.GPIO libjpeg8-dev
sudo pip3 install python-escpos

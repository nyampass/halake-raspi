# references
# http://qiita.com/ihgs/items/34eefd8d01c570e92984

CURRENT_DIR=`pwd`

# ready
sudo apt-get update
sudo apt-get upgrade
git clone git://git.drogon.net/wiringPi
cd wiringPi
./build
cd ../
sudo apt-get install python-dev python-setuptools
git clone https://github.com/Gadgetoid/WiringPi2-Python.git
cd WiringPi2-Python
sudo python setup.py install

#
# install nycpy
#

# related packages
sudo apt-get install -y python-pip python-usb bzr
sudo pip libusb1 pyserial

# download
mkdir ~/nycpy
cd ~/nycpy
bzr branch lp:nfcpy trunk

# set path for global
cd ~/nycpy/trunk/nfc
sudo ln -s `pwd` /usr/local/lib/python2.7/dist-packages/

# get back to first directory
cd $CURRENT_DIR

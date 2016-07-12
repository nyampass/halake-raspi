# references
# http://qiita.com/ihgs/items/34eefd8d01c570e92984

CURRENT_DIR=`pwd`

# ready
sudo apt-get update
sudo apt-get upgrade

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

#!/bin/bash

CURRENT_DIR=$( cd `dirname $0`; pwd )

${CURRENT_DIR}/../src/gatein-with-felica.py &
# Add sleep for receipt printer because initial event get request cause error without sleep.
sleep 20; ${CURRENT_DIR}/../src/receipt-printer.py &

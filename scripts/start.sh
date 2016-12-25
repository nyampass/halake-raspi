#!/bin/bash

CURRENT_DIR=$( cd `dirname $0`; pwd )

${CURRENT_DIR}/../src/gatein-with-felica.py &
${CURRENT_DIR}/../src/receipt-printer.py &

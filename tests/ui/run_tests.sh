#!/bin/bash

HOST=${HOST:-localhost}
PORT=${PORT:-8001}
USERNAME=${USERNAME:-root}

# ask for password if not passed
if [ -z $PASSWORD ]; then
    echo "Type password for host ${USERNAME}@${HOST}"
    read -s PASSWORD
fi

# ../../../../../../ is wok root

HOST=${HOST} PASSWORD=${PASSWORD} USERNAME=${USERNAME} PORT=${PORT} \
PYTHONPATH=$PYTHONPATH:../../../../../../tests/ui/ python3 -m pytest

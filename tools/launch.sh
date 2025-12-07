#!/bin/bash
# Launches server app

ARGS=("$@")
ADDRESS="0.0.0.0"
PORT=9000

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_DIR/../
poetry run python manage.py runserver $ADDRESS:$PORT $@
PID=$!
wait $PID

RET=$?
let SIGNAL_NO=$RET-128

exit $RET


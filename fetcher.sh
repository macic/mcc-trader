#!/bin/bash
app="/home/macic/develop/mcc-trader/"
logdir="/var/log/mcc-trader/"
source ${app}venv/bin/activate
${app}venv/bin/python ${app}fetcher.py read_ohlc_from_kraken --symbol=ETHEUR --interval=5 --ts_start=15 >>${logdir}fetcher.log 2>&1
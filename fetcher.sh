#!/bin/bash
  2 app="/home/macic/develop/mcc-trader/"
  3 logdir="/var/log/mcc-trader/"
  4 source ${app}venv/bin/activate
  5 ${app}venv/bin/python ${app}fetcher.py read_ohlc_from_kraken --symbol=ETHEUR --interval=5 --ts_start=15 >>${logdir}fetcher.log 2>&1
#!/bin/bash

xpra start :100 \
  --start-child=openbox \
  --start-child=gnucash \
  --bind-tcp=0.0.0.0:14500 \
  --html=on \
  --sharing=no

tail -f /dev/null

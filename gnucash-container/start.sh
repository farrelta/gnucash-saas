#!/bin/bash

# Ensure /data directory exists with correct permissions
mkdir -p /data
chown -R 1000:1000 /data 2>/dev/null || true

# Set GnuCash data directory
export XDG_DATA_HOME=/data
export HOME=/data

xpra start :100 \
  --start-child=openbox \
  --start-child=gnucash \
  --bind-tcp=0.0.0.0:14500 \
  --html=on \
  --sharing=no \
  --daemon=no

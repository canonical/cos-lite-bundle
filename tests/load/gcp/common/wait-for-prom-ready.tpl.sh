#!/bin/bash
set -eu

READY=0
until [ $READY -eq 1 ]; do
  READY=$(curl -s --connect-timeout 2 --max-time 5 ${PROM_EXTERNAL_URL}/-/ready | grep -iF 'is ready' | wc -l)
  sleep 5
done

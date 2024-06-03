#!/bin/bash
set -eu

READY=0
until [ $READY -eq 1 ]; do
  READY=$(curl -s --connect-timeout 2 --max-time 5 ${GRAFANA_EXTERNAL_URL}/api/health | grep -F 'version' | wc -l)
  # READY=$(juju status grafana --format=json | jq -r '.applications.grafana."application-status".current' | grep -F 'active' | wc -l)
  sleep 5
done

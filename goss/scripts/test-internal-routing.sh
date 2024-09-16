#!/bin/bash

# Obtain the alertmanager_url from Loki's loki-local-config.yaml and test routability from Loki's charm container

MODEL_NAME="$1"
LOKI_APP_NAME="$2"
ALERTMANAGER_APP_NAME="$3"

alertmanager_url=$(juju ssh --container loki ${LOKI_APP_NAME}/0 cat /etc/loki/loki-local-config.yaml | yq -r '.ruler.alertmanager_url')
status_code=$(juju ssh ${LOKI_APP_NAME}/0 "python3 -c \"import urllib.request; response = urllib.request.urlopen('${alertmanager_url}'); print(response.getcode())\"")

echo "Status code: $status_code"
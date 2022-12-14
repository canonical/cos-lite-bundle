#!/bin/bash
set -eu

while true; do
  # Going through `current` directly because microk8s-kubectl.wrapper creates subprocesses which expect a login session
  /snap/microk8s/current/kubectl --kubeconfig /var/snap/microk8s/current/credentials/client.config top pod -n ${JUJU_MODEL_NAME} --no-headers
  sleep 30
done

#!/bin/bash
systemctl disable systemd-tmpfiles-clean.timer --now
microk8s status --wait-ready
sh -c "until microk8s.kubectl rollout status deployments/hostpath-provisioner -n kube-system -w; do sleep 5; done"
sh -c "until microk8s.kubectl rollout status deployments/coredns -n kube-system -w; do sleep 5; done"
sh -c "until microk8s.kubectl rollout status daemonsets/nginx-ingress-microk8s-controller -n ingress -w; do sleep 5; done"
sudo -u ubuntu juju bootstrap --no-gui microk8s uk8s
sudo -u ubuntu juju add-model --config logging-config="<root>=WARNING; unit=DEBUG" --config update-status-hook-interval="60m" lma-load-test


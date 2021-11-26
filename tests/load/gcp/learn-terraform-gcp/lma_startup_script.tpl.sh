#!/bin/bash
systemctl disable systemd-tmpfiles-clean.timer --now
microk8s status --wait-ready
microk8s.enable storage dns ingress

IPADDR=$(ip -4 route | grep default | grep -oP 'src \K\S+')

# Occasionally, enabling metallb fails with the following error:
# The connection to the server 127.0.0.1:16443 was refused - did you specify the right host or port?
# Try enabling it a loop:
until microk8s.enable metallb:$IPADDR-$IPADDR; do sleep 5; done

sh -c "until microk8s.kubectl rollout status deployments/hostpath-provisioner -n kube-system -w; do sleep 5; done"
sh -c "until microk8s.kubectl rollout status deployments/coredns -n kube-system -w; do sleep 5; done"
sh -c "until microk8s.kubectl rollout status daemonsets/nginx-ingress-microk8s-controller -n ingress -w; do sleep 5; done"
sh -c "until microk8s.kubectl rollout status daemonset.apps/speaker -n metallb-system -w; do sleep 5; done"

# workaround for
# ERROR resolving microk8s credentials: max duration exceeded: secret for service account "juju-credential-microk8s" not found
# Ref: https://github.com/charmed-kubernetes/actions-operator/blob/main/src/bootstrap/index.ts
microk8s kubectl create serviceaccount test-sa
timeout 600 sh -c "until microk8s kubectl get secrets | grep -q test-sa-token-; do sleep 5; done"
microk8s kubectl delete serviceaccount test-sa

SCRAPE_TARGETS="${URL_AVALANCHE}:9001"
for ((i = 2 ; i <= ${NUM_SCRAPE_TARGETS} ; i++)) ; do SCRAPE_TARGETS="$SCRAPE_TARGETS,${URL_AVALANCHE}:$((9000 + $i))"; done

sudo -u ubuntu juju bootstrap --no-gui microk8s uk8s
sudo -u ubuntu juju add-model --config logging-config="<root>=WARNING; unit=DEBUG" --config update-status-hook-interval="60m" lma-load-test
sudo -u ubuntu juju deploy --channel=edge lma-light --trust
sudo -u ubuntu juju deploy --channel=edge --trust prometheus-scrape-target-k8s scrape-target --config targets=$SCRAPE_TARGETS
sudo -u ubuntu juju deploy --channel=edge --trust prometheus-scrape-config-k8s scrape-config --config scrape-interval=60s --config scrape-timeout=55s
sudo -u ubuntu juju relate scrape-config:configurable-scrape-jobs scrape-target:metrics-endpoint
sudo -u ubuntu juju relate scrape-config:metrics-endpoint prometheus:metrics-endpoint

microk8s.kubectl apply -f - <<'EOY'
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: prom-ingress
  namespace: lma-load-test
  annotations:
    nginx.ingress.kubernetes.io/use-regex: "true"
    nginx.ingress.kubernetes.io/rewrite-target: /$1
spec:
  ingressClassName: public
  rules:
  - http:
      paths:
      - path: /prom/(.*)
        pathType: Prefix
        backend:
          service:
            name: prometheus
            port:
              number: 9090
      - path: /loki/(.*)
        pathType: Prefix
        backend:
          service:
            name: loki
            port:
              number: 3100
EOY


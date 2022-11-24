set -eux

# install deps
DEBIAN_FRONTEND=noninteractive apt -y upgrade

# disable swap
sysctl -w vm.swappiness=0
echo "vm.swappiness = 0" | tee -a /etc/sysctl.conf
swapoff -a

# disable unnecessary services
systemctl disable apport.service apport-autoreport.service  --now
systemctl disable apt-daily.service apt-daily.timer --now
systemctl disable apt-daily-upgrade.service apt-daily-upgrade.timer --now
systemctl disable unattended-upgrades.service --now
systemctl disable motd-news.service motd-news.timer --now
systemctl disable bluetooth.target --now
systemctl disable ua-timer.timer ua-timer.service ubuntu-advantage.service --now
systemctl disable systemd-tmpfiles-clean.timer --now

# start services
systemctl daemon-reload
sed -i 's/ENABLED="false"/ENABLED="true"/' /etc/default/sysstat
systemctl restart sysstat sysstat-collect.timer sysstat-summary.timer
systemctl start node-exporter.service

# setup microk8s and bootstrap
adduser ubuntu microk8s
microk8s status --wait-ready
microk8s enable dns:$(grep nameserver /run/systemd/resolve/resolv.conf | awk '{print $2}')
microk8s.enable storage ingress
# wait for addons to become available
microk8s.kubectl rollout status deployments/hostpath-provisioner -n kube-system -w --timeout=600s

# Patch hostpath to allocate less resources (https://github.com/canonical/microk8s-core-addons/pull/73)
kubectl patch deployment hostpath-provisioner -n kube-system -p '{"spec": {"template": {"spec": {"containers": [{"name":"hostpath-provisioner", "image": "cdkbot/hostpath-provisioner:1.3.0" }] }}}}'
microk8s.kubectl rollout status deployments/hostpath-provisioner -n kube-system -w --timeout=600s

microk8s.kubectl rollout status deployments/coredns -n kube-system -w --timeout=600s
microk8s.kubectl rollout status daemonsets/nginx-ingress-microk8s-controller -n ingress -w --timeout=600s
microk8s.enable metrics-server
microk8s.kubectl rollout status deployment.apps/metrics-server -n kube-system -w --timeout=600s

# To prevent metallb from failing with the following error:
# The connection to the server 127.0.0.1:16443 was refused - did you specify the right host or port?
# the metallb addon must be enabled only after the dns addon was rolled out
# https://github.com/ubuntu/microk8s/issues/2770#issuecomment-984346287
IPADDR=$(ip -4 -j route | jq -r '.[] | select(.dst | contains("default")) | .prefsrc')
microk8s.enable metallb:$IPADDR-$IPADDR
microk8s.kubectl rollout status daemonset.apps/speaker -n metallb-system -w --timeout=600s

# workaround for
# ERROR resolving microk8s credentials: max duration exceeded: secret for service account "juju-credential-microk8s" not found
# Ref: https://github.com/charmed-kubernetes/actions-operator/blob/main/src/bootstrap/index.ts
# Not needed for uk8s 1.24
# microk8s.kubectl create serviceaccount test-sa
# timeout 600 sh -c "until microk8s.kubectl get secrets | grep -q test-sa-token-; do sleep 5; done"
# microk8s.kubectl delete serviceaccount test-sa

# prep juju
sudo -u ubuntu juju bootstrap --no-gui --agent-version=2.9.34 microk8s uk8s
sudo -u ubuntu juju add-model --config logging-config="<root>=WARNING; unit=DEBUG" --config update-status-hook-interval="5m" ${JUJU_MODEL_NAME}
sudo -u ubuntu juju deploy --channel=edge cos-lite --trust --overlay /run/overlay-load-test.yaml --overlay /run/prom-latest.yaml --trust

# Temporary manual ingress setup
# TODO remove after bundle updates
#sudo -u ubuntu juju config traefik external_hostname=${COS_APPLIANCE_HOSTNAME}
# TODO remove after grafana ingress implemented
sleep 60  # blind sleep to avoid: Error from server (NotFound): statefulsets.apps "grafana" not found
microk8s.kubectl rollout status statefulset.apps/grafana -n ${JUJU_MODEL_NAME} -w --timeout=600s
#kubectl -n ${JUJU_MODEL_NAME} expose pod grafana-0 --port=3000 --target-port=3000 --name=grafana-expose-service
# nohup kubectl -n ${JUJU_MODEL_NAME} port-forward --address 0.0.0.0 grafana-0 3000:3000 &

# install ops agent for observability
#echo '"projects/${PROJECT}/zones/${ZONE}/instances/${INSTANCE}","[{""type"":""ops-agent""}]"' >> agents_to_install.csv && \
#curl -sSO https://dl.google.com/cloudagents/mass-provision-google-cloud-ops-agents.py && \
#python3 mass-provision-google-cloud-ops-agents.py --file agents_to_install.csv

#curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
#sudo bash add-google-cloud-ops-agent-repo.sh --also-install

# start services
# Waiting for prom here because systemd would timeout waiting for the unit to become active/idle:
#   Job for prometheus-stdout-logger.service failed because a timeout was exceeded.
/run/wait-for-prom-ready.sh
systemctl start prometheus-stdout-logger.service
systemctl start pod-top-logger.service

# wait for grafana to become active
# TODO re-enable "wait for grafana" after ingress works again
# /run/wait-for-grafana-ready.sh
systemctl start cos-lite-rest-server.service

# force reldata reinit in case files appeared on disk after the last hook fired
sudo -u ubuntu juju run-action cos-config/0 sync-now --wait

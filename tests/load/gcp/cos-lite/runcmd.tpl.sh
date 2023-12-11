set -eux

# install deps
DEBIAN_FRONTEND=noninteractive apt -y upgrade

pip3 install flask lightkube

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
usermod -a -G snap_microk8s ubuntu
microk8s status --wait-ready
microk8s enable dns:$(grep nameserver /run/systemd/resolve/resolv.conf | awk '{print $2}')
microk8s.enable hostpath-storage
# wait for addons to become available
microk8s.kubectl rollout status deployments/hostpath-provisioner -n kube-system -w --timeout=600s

microk8s.kubectl rollout status deployments/coredns -n kube-system -w --timeout=600s
microk8s.enable metrics-server
microk8s.kubectl rollout status deployment.apps/metrics-server -n kube-system -w --timeout=600s

# To prevent metallb from failing with the following error:
# The connection to the server 127.0.0.1:16443 was refused - did you specify the right host or port?
# the metallb addon must be enabled only after the dns addon was rolled out
# https://github.com/ubuntu/microk8s/issues/2770#issuecomment-984346287
IPADDR=$(ip -4 -j route get 2.2.2.2 | jq -r '.[] | .prefsrc')
microk8s.enable metallb:$IPADDR-$IPADDR
microk8s.kubectl rollout status daemonset.apps/speaker -n metallb-system -w --timeout=600s

# prep juju
# For some reason, in the minimal cloud image, the group and owner of the ubuntu user is root
# TODO: try to add "owner" and "defer" to "write_files" to prevent from cloud init to set $HOME to
#  be owned by root:root.
#  https://canonical-cloud-init.readthedocs-hosted.com/en/latest/reference/modules.html#write-files
chgrp -R ubuntu /home/ubuntu
chown -R ubuntu /home/ubuntu

# https://bugs.launchpad.net/juju/+bug/1988355
sudo -u ubuntu mkdir -p /home/ubuntu/.local/share/juju
sudo -u ubuntu juju bootstrap --agent-version=3.1.6 microk8s uk8s
sudo -u ubuntu juju add-model --config logging-config="<root>=WARNING; unit=DEBUG" --config update-status-hook-interval="5m" ${JUJU_MODEL_NAME}
sudo -u ubuntu juju deploy --channel=edge cos-lite --trust --overlay /home/ubuntu/overlay-load-test.yaml --trust



# start services

# Temporary workaround for grafana giving 404 (TODO remove when fixed)
# Need to sleep a bit, otherwise:
# Error from server (NotFound): statefulsets.apps "grafana" not found
sleep 120
microk8s.kubectl rollout status statefulset.apps/grafana -n ${JUJU_MODEL_NAME} -w --timeout=600s
#sudo -u ubuntu juju remove-relation grafana:ingress traefik
#sleep 30
#sudo -u ubuntu juju relate grafana:ingress traefik


# https://bugs.launchpad.net/juju/+bug/2045317
microk8s.kubectl rollout status statefulset.apps/loki -n ${JUJU_MODEL_NAME} -w --timeout=600s
sudo -u ubuntu juju refresh --switch loki-k8s --channel=edge/325 loki  # Expires at 2023-12-30T00:00:00Z


# wait for grafana to become active
/run/wait-for-grafana-ready.sh
systemctl start cos-lite-rest-server.service

# force reldata reinit in case files appeared on disk after the last hook fired
sudo -u ubuntu juju run cos-config/0 sync-now

# Waiting for prom here because systemd would timeout waiting for the unit to become active/idle:
#   Job for prometheus-stdout-logger.service failed because a timeout was exceeded.
/run/wait-for-prom-ready.sh
systemctl start prometheus-stdout-logger.service
systemctl start pod-top-exporter.service

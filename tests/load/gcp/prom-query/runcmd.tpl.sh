set -eux

# TODO: try to add "owner" and "defer" to "write_files" to prevent from cloud init to set $HOME to
#  be owned by root:root.
#  https://canonical-cloud-init.readthedocs-hosted.com/en/latest/reference/modules.html#write-files
chown -R ubuntu /home/ubuntu
chgrp -R ubuntu /home/ubuntu

# install deps
python3 -m pip install locust splinter selenium webdriver_manager

apt remove -y nodejs npm --auto-remove
snap install --classic node --channel=16/stable
npm i -g element-cli@2.0.4
sudo -u ubuntu npx -y playwright@1.27.1 install-deps
# sudo -u ubuntu npm install @playwright/test
sudo -u ubuntu npx -y playwright@1.27.1 install

# For some reason, npx installs chrome in one folder, but element looks for it in another
# (non-existing). Symlink and be done with it.
TARGET="$(find /home/ubuntu/.cache/ms-playwright/ -maxdepth 1 -type d -name "chromium-*" | head -1)"
ln -s "$TARGET" /home/ubuntu/.cache/ms-playwright/chromium
ln -s "$TARGET" /home/ubuntu/.cache/ms-playwright/chromium-1084

# wait until the cos-lite node is up
timeout 1800 bash -c "until curl -s --connect-timeout 2.0 --max-time 5 ${PROM_URL}/api/v1/targets; do sleep 5; done"

# wait until the cos-lite rest server is up
timeout 1800 bash -c "until curl -s --connect-timeout 2.0 --max-time 5 ${COS_URL}:8081/helper/grafana/password; do sleep 5; done"

# without piping to jq, curl would return successfully with "nginx 404 not found"
# TARGETS=0; until [ $TARGETS -gt 1 ]; do TARGETS=$(curl -s --connect-timeout 2.0 ${PROM_URL}/api/v1/targets | jq '.data.activeTargets[].health' 2>/dev/null | wc -l); sleep 5; done

timeout 600 bash << 'EOF'
set -euxo pipefail

_num_targets() {
echo "$(curl -s --connect-timeout 2 --max-time 5 ${PROM_URL}/api/v1/targets \
        | jq '.data.activeTargets[].health' \
        | wc -l)"
}

until [[ "$(_num_targets)" -gt 1 ]]; do sleep 5; done
EOF

timeout 600 bash << 'EOF'
set -euxo pipefail

_num_dashboards() {
GRAFANA_ADMIN_PASSWORD=$(curl -s --connect-timeout 2.0 --max-time 5 ${COS_URL}:8081/helper/grafana/password)
echo "$(curl -s --connect-timeout 2 --max-time 5 --user admin:$${GRAFANA_ADMIN_PASSWORD} ${GRAFANA_URL}/api/search \
        | jq '.[].uid' \
        | wc -l)"
}
until [[ "$(_num_dashboards)" -gt 0 ]]; do sleep 5; done
EOF

GRAFANA_ADMIN_PASSWORD=$(curl -s --connect-timeout 2.0 --max-time 5 ${COS_URL}:8081/helper/grafana/password)
sed -i "s/GRAFANA_ADMIN_PASSWORD_TO_SUBSTITUTE_BY_CLOUD_INIT/$${GRAFANA_ADMIN_PASSWORD}/" /home/ubuntu/prom-query-grafana-dashboards.ts

# now that prom is reachable and scraping, and grafana sees dashboards, start locust
systemctl daemon-reload
systemctl start flood-element-grafana.service
systemctl start node-exporter.service

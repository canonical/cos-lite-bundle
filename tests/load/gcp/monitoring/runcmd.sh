set -eux

systemctl daemon-reload
systemctl start grafana-agent.service

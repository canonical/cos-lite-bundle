set -eux
mkdir -p /go/.cache /go/bin && HOME=/go GOPATH=/go GOCACHE=/go/.cache go install github.com/prometheus-community/avalanche/cmd@19b624b
mv /go/bin/cmd /usr/bin/avalanche

systemctl daemon-reload
systemctl start avalanche-targets.target
systemctl start node-exporter.service

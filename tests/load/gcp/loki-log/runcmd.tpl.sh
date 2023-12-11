set -eux

# install deps
python3 -m pip install locust logfmter Faker charset-normalizer

# wait until the cos-lite node is up
timeout 1800 bash -c "until curl -s --connect-timeout 2.0 --max-time 5 ${LOKI_URL}/ready; do sleep 5; done"

timeout 1800 bash << 'EOF'
set -eux

_is_ready() {
echo "$(curl -s --connect-timeout 2 --max-time 5 ${LOKI_URL}/ready \
        | grep '^ready$' \
        | wc -l)"
}

until [[ "$(_is_ready)" -eq 1 ]]; do sleep 5; done
EOF

# now that loki is really ready, start locust
systemctl daemon-reload
systemctl start locust-loggers.target
systemctl start node-exporter.service

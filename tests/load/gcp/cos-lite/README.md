## Manual verifications
To see how the cloud-config file was rendered,

```shell
sudo cat /var/lib/cloud/instance/cloud-config.txt
```

```shell
# check cloud-init completed
cat /var/log/cloud-init-output.log

# check all units are up
juju status

# check avalanche vm is reachable
curl -s http://avalanche.us-central1-a.c.lma-light-load-testing.internal:9001/metrics | grep -v '^#' | wc -l

# check service status
systemctl status node-exporter
systemctl status prometheus-stdout-logger
systemctl status pod-top-exporter

# check ingress is working
curl -s http://pd-ssd-4cpu-8gb.us-central1-a.c.lma-light-load-testing.internal/cos-lite-load-test-prometheus-0/api/v1/targets | jq ".data.activeTargets[].scrapeUrl"

# check helper app is exposing grafana admin password
curl localhost:8081/helper/grafana/password

# check number of logs Loki processed
curl -s "http://pd-ssd-4cpu-8gb.us-central1-a.c.lma-light-load-testing.internal/cos-lite-load-test-loki-0/metrics" | grep log_messages_total
curl -s "http://pd-ssd-4cpu-8gb.us-central1-a.c.lma-light-load-testing.internal/cos-lite-load-test-loki-0/metrics" | grep loki_ingester_wal_records_logged_total
curl -s "http://pd-ssd-4cpu-8gb.us-central1-a.c.lma-light-load-testing.internal/cos-lite-load-test-loki-0/metrics" | grep -v '^# ' | grep -v '^go_' | sort -k 2 -g

# make sure loki label cardinality is low
curl -G -s  "http://pd-ssd-4cpu-8gb.us-central1-a.c.lma-light-load-testing.internal/cos-lite-load-test-loki-0/loki/api/v1/labels" | jq

# check how much space prometheus is taking
kubectl exec -n cos-lite-load-test prometheus-0 -c prometheus -- du -d 1 -h /var/lib/prometheus | sort -h

# visual inspection of the load-test dashboard
# - metrics and logs are displayed?
```

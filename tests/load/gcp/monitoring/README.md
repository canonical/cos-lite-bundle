## Manual verifications
To see how the cloud-config file was rendered,

```shell
sudo cat /var/lib/cloud/instance/cloud-config.txt
```

```shell
# check service status
systemctl status grafana-agent
journalctl -u grafana-agent --follow

# check reachability
ping pd-ssd-4cpu-8gb.us-central1-a.c.lma-light-load-testing.internal
curl http://pd-ssd-4cpu-8gb.us-central1-a.c.lma-light-load-testing.internal/cos-lite-load-test-prometheus-0/api/v1/labels

# check targets
curl localhost:12345/agent/api/v1/metrics/targets | jq
```

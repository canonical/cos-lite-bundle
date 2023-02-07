## Manual verifications
To see how the cloud-config file was rendered,

```shell
sudo cat /var/lib/cloud/instance/cloud-config.txt
```

```shell
# check service status
systemctl status flood-element-grafana
pgrep -laf chrome
journalctl -u flood-element-grafana -f
tail -f /var/log/syslog

# check COS appliance and prom are reachable
ping pd-ssd-4cpu-8gb.us-central1-a.c.lma-light-load-testing.internal
curl http://pd-ssd-4cpu-8gb.us-central1-a.c.lma-light-load-testing.internal/cos-lite-load-test-prometheus-0/api/v1/labels

# check network rates
sudo iftop -i ens4 -f "host pd-ssd-4cpu-8gb.c.lma-light-load-testing.internal"
```

### Manually run the test in your browser

First, copy rendered files from the VM:

```
$ scp -i ~/secrets/cos-lite-load-testing-ssh \
  -o "UserKnownHostsFile=/dev/null" \
  -o "StrictHostKeyChecking no" \
  ubuntu@35.184.199.203:/home/ubuntu/prom-query-grafana-dashboards.config.js prom-query-grafana-dashboards.config.js

$ scp -i ~/secrets/cos-lite-load-testing-ssh \
  -o "UserKnownHostsFile=/dev/null" \
  -o "StrictHostKeyChecking no" \
  ubuntu@35.184.199.203:/home/ubuntu/prom-query-grafana-dashboards.ts prom-query-grafana-dashboards.ts
```

Set up an ssh tunnel with DNS lookups:
```
sudo sshuttle --dns -r ubuntu@35.184.199.203 0/0 --ssh-cmd 'ssh -o "UserKnownHostsFile=/dev/null" -o "StrictHostKeyChecking no" -i /home/user/secrets/cos-lite-load-testing-ssh'
```

Run the test (a browser window should pop up):
```
npx @flood/element-cli run prom-query-grafana-dashboards.ts --config prom-query-grafana-dashboards.config.js --no-headless
```

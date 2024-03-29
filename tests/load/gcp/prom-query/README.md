## Manual verifications
To see how the cloud-config file was rendered,

```shell
sudo cat /var/lib/cloud/instance/cloud-config.txt
```

```shell
# check cloud-init completed
cat /var/log/cloud-init-output.log

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

### Manually run the test in your browser (zombie)

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

Alternatively, change the login hostname to `localhost:8080` and set up an ssh tunnel with the `-L` flag:

```
ssh -i ~/secrets/cos-lite-load-testing-ssh \
    -o "UserKnownHostsFile=/dev/null" \
    -o "StrictHostKeyChecking no" \
    -L localhost:8080:10.128.0.7:80 \
    ubuntu@35.184.199.203
```

- `34.42.192.203` is the GCP vm IP
- `10.128.0.7:80` is the traefik address inside the GCP vm

In the *.js file, replace the address in `await browser.visit(...)` with
`localhost:8080`.

Run the test (a browser window should pop up):
```
npx @flood/element-cli run prom-query-grafana-dashboards.ts --config prom-query-grafana-dashboards.config.js --no-headless
```

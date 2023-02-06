## Manual verifications
To see how the cloud-config file was rendered,

```shell
sudo cat /var/lib/cloud/instance/cloud-config.txt
```

```shell
# check service status
systemctl status locust-loggers.target
journalctl -u locust@0 -f

# check network rates
sudo iftop -i ens4 -f "host pd-ssd-4cpu-8gb.c.lma-light-load-testing.internal"
```

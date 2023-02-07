## Manual verifications
To see how the cloud-config file was rendered,

```shell
sudo cat /var/lib/cloud/instance/cloud-config.txt
```

```shell
# check service status
systemctl status avalanche-targets.target

# count number of scrape targets
pgrep avalanche | wc -l

# count number of datapoints a scrape target is offering
# (each series id is in its own line)
curl localhost:9001/metrics | grep -v '^#' | wc -l
```

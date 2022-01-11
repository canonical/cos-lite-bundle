## Load tests on Google Cloud Platform (GCP)

The purpose of these load tests is to produce performance anchors for lma-light
operating as a standalone appliance, for the following resource matrix:

| Disk type | vCPUs | Mem, GB |
|:---------:|:-----:|:-------:|
|   ssd     |   2   |    4    |
|   ssd     |   2   |    8    |
|   ssd     |   4   |    8    |
|  standard |   2   |    4    |
|  standard |   2   |    8    |
|  standard |   4   |    8    |

To start a load test:

```shell
terraform apply -var-file="var_ssd-2cpu-8gb.tfvars"

# or, override some of the variables

terraform apply -var-file="var_ssd-2cpu-8gb.tfvars" -var="ncpus=4" -var="gbmem=16"

# or, do not use a var-file at all

terraform apply -var="disk_type=pd-ssd" -var="num_avalanche_targets=3" -var="ncpus=2" -var="gbmem=8"
```

which will create three vm instances:
- avalanche
- locust
- pd-ssd-2cpu-8gb

Similarly, to destroy,

```shell
terraform destroy -var-file="var_ssd-2cpu-8gb.tfvars"
```

Note that only one load test can run at a time. This is because terraform does not support
parametrizing resource names.

To ssh into a vm instance,

```shell
ssh -i ~/secrets/lma-light-load-testing-ssh \
  -o "UserKnownHostsFile=/dev/null" \
  -o "StrictHostKeyChecking no" \
  ubuntu@$(terraform output ip_nat_vm_lma_appliance | xargs -n1 echo)
```

### Manual verifications
#### Avalanche (prom_scrape)
```shell
# check service status
systemctl status avalanche-targets.target

# count number of scrape targets
pgrep avalanche | wc -l

# count number datapoints a scrape target is offering (each series id is in its own line)
curl localhost:9001/metrics | grep -v '^#' | wc -l
```

#### Locust (prom_query)
```shell
# check service status
systemctl status locust

# check lma appliance and prom are reachable
ping http://pd-ssd-4cpu-8gb.us-central1-a.c.lma-light-load-testing.internal
curl http://pd-ssd-4cpu-8gb.us-central1-a.c.lma-light-load-testing.internal/prom/api/v1/labels

# follow the progress of the load test
journalctl -u locust -f
```

#### LMA appliance
```shell
# check cloud-init completed
cat /var/log/cloud-init-output.log

# check all units are up
juju status

# check avalanche vm is reachable
curl http://avalanche.us-central1-a.c.lma-light-load-testing.internal:9001/metrics | wc -l

# check service status
systemctl status node-exporter
systemctl status prometheus-stdout-logger
systemctl status pod-top-logger

# check ingress is working
curl localhost/prom/api/v1/targets
```


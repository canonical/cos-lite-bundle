# Usage Workflow

## Installation
1. Install the [Goss binary](https://goss.readthedocs.io/en/stable/installation/).

## Fetch the goss.yaml files
To validate a model, `goss.yaml` files (customised to a specific deployment) are required. These files can be decentralised, but must exist on the FS for Goss validation. For cos-lite-bundle these files exist in [cos-lite-bundle/goss](https://github.com/canonical/cos-lite-bundle/tree/investigate-goss/goss).

2. `git clone --branch investigate-goss https://github.com/canonical/cos-lite-bundle.git`

## Test with Goss
3. `juju add-model cos-model`
4. `juju deploy cos-lite --trust`
5. `juju status --watch 1s` -> wait for `active/idle`
6. `goss -g cos-lite-bundle/goss/goss.yaml v -f documentation`

Sample results:
```
Command: loki-pod-container-healthy: stdout: matches expectation: ["true"]
Command: loki-pod-status-healthy: stdout: matches expectation: ["true"]
Command: relation-grafana-loki: stdout: matches expectation: ["grafana"]
Command: grafana-pebble: stdout: matches expectation: ["healthy"]
...
Command: traefik-pebble: stdout: matches expectation: ["healthy"]
Command: loki-reachable-via-ingress-url: stdout: matches expectation: ["ready"]
Command: grafana-related-dashboards: stdout: matches expectation: ["The alertmanager dashboard UID is a subset of the Grafana dashboard UIDs."]

Total Duration: 2.375s
Count: 22, Failed: 0, Skipped: 0
```

## Contributing

1. `git clone --branch investigate-goss https://github.com/canonical/cos-lite-bundle.git`
2. Modify the contents of the goss directory according to your needs.
   1. See the docs for [quickstart](https://goss.readthedocs.io/en/stable/quickstart/), [goss-test-creation](https://goss.readthedocs.io/en/stable/gossfile/#goss-test-creation), [gossfile](https://goss.readthedocs.io/en/stable/gossfile/#gossfile), and [complex examples](https://goss.readthedocs.io/en/stable/gossfile/#examples).

[OPENG-2677]: https://warthogs.atlassian.net/browse/OPENG-2677?atlOrigin=eyJpIjoiNWRkNTljNzYxNjVmNDY3MDlhMDU5Y2ZhYzA5YTRkZjUiLCJwIjoiZ2l0aHViLWNvbS1KU1cifQ

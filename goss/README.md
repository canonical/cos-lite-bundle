# Usage Workflow

## Installation
1. Install the [Goss binary](https://goss.readthedocs.io/en/stable/installation/) or `sudo snap install goss --classic`

## Validate a Model/Deployment
To validate a model, `goss.yaml` files (customised to a specific deployment) are required. These can be an artifact or [centrally stored](https://docs.google.com/document/d/1EG71A2pJ244PQRaGVzGj7Mx2B_bzE4U_OSqx4eeVI1E/edit#heading=h.w2r1144djmlw).

### Via CI Artifact
1. Download the [goss-artifact](https://github.com/canonical/cos-lite-bundle/actions/runs/11001501181/artifacts/1968217647).
    * Note:
        1. This [CI step](https://github.com/canonical/cos-lite-bundle/blob/0a74e1354a1e77cc55dcd6dcda7d0ee4d45c78b9/.github/workflows/ci.yaml#L109) creates a .zip file of the `goss` dir as an artifact.
        2. Artifacts are generated only on RELEASE
        3. Programmatically use the [GH Artifacts API](https://docs.github.com/en/rest/actions/artifacts?apiVersion=2022-11-28)
            * E.g. get latest artifact: `curl -sL 'https://api.github.com/repos/canonical/cos-lite-bundle/actions/artifacts' | jq -r '.artifacts[0].archive_download_url'`
2. Move the artifact to the host context where `goss validate` will be run and unzip.

<details>
<summary>Centrally Stored YAMLs</summary>

Via Sparse Checkout
1. `git init goss && cd goss`
2. `git remote add -f origin https://github.com/canonical/cos-lite-bundle.git`
3. `git config core.sparseCheckout true`
4. `echo "goss/*" > .git/info/sparse-checkout`
5. `git pull origin investigate-goss`

</details>


### Test with Goss
#### Manually
1. `juju add-model cos-model`
2. `juju deploy cos-lite --trust`
3. `juju status --watch 1s` -> wait for `active/idle`
4. `goss -g goss/goss.yaml --vars goss/vars.yaml v -f documentation`


#### Tox Integration Tests
2. `tox -e render-edge`
3. `tox -e integration`

Expected results:
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
3. See the docs for [quickstart](https://goss.readthedocs.io/en/stable/quickstart/), [goss-test-creation](https://goss.readthedocs.io/en/stable/gossfile/#goss-test-creation), [gossfile](https://goss.readthedocs.io/en/stable/gossfile/#gossfile), and [complex examples](https://goss.readthedocs.io/en/stable/gossfile/#examples).

[OPENG-2677]: https://warthogs.atlassian.net/browse/OPENG-2677?atlOrigin=eyJpIjoiNWRkNTljNzYxNjVmNDY3MDlhMDU5Y2ZhYzA5YTRkZjUiLCJwIjoiZ2l0aHViLWNvbS1KU1cifQ

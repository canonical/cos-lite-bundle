# Overview

This documents explains the processes and practices recommended for
contributing enhancements to the COS Lite bundle.

- Generally, before developing enhancements to this charm, you should consider
  [opening an issue](https://github.com/canonical/cos-lite-bundle) explaining
  your use case.
- If you would like to chat with us about your use cases or proposed
  implementation, you can reach us on the
  [Charmhub Mattermost](https://chat.charmhub.io/charmhub/channels/charm-dev)
  or [Discourse](https://discourse.charmhub.io/).
- All enhancements require review before being merged.
  Apart from code quality and test coverage, the review will also take into
  account the Juju administrator user experience using the bundle.

## Development

There are four charms used for development:
- prometheus
- alertmanager
- grafana
- loki
- avalanche

### Deploy with local charms

To deploy the bundle using only/some local charms you need to render the
[`bundle.yaml.j2`](bundle.yaml.j2) template and then deploy the rendered bundle
as usual.

#### Render template using the rendering script
You can render and deploy a production bundle using:

```shell
# generate and activate a virtual environment with dependencies
tox -e integration --notest
source .tox/integration/bin/activate

./render_bundle.py bundle.yaml
juju deploy ./bundle.yaml
```

To render the bundle for testing:

```shell
./render_bundle.py bundle.yaml --channel=edge
```

This would include a tester charm (avalanche) and an overlay section with offers.

Optionally, you may render the template with local charms, for example:

```shell
./render_bundle.py bundle.yaml --channel=edge \
  --traefik=$(pwd)/../traefik-k8s-operator/traefik-k8s_ubuntu-20.04-amd64.charm \
  --prometheus=$(pwd)/../prometheus-k8s-operator/prometheus-k8s_ubuntu-20.04-amd64.charm \
  --alertmanager=$(pwd)/../alertmanager-k8s-operator/alertmanager-k8s_ubuntu-20.04-amd64.charm \
  --grafana=$(pwd)/../grafana-k8s-operator/grafana-k8s_ubuntu-20.04-amd64.charm \
  --loki=$(pwd)/../loki-operator/loki-k8s-operator_ubuntu-20.04-amd64.charm
```


## Testing
Integration tests render the
[`bundle-testing.yaml.j2`](tests/integration/bundle-testing.yaml.j2) template
with the charm names/paths to use for the integration tests.
By default, all charms are deployed from charmhub. Alternatively, you can pass
local paths (or alternative charm names) as
[command line arguments](tests/integration/conftest.py) to pytest.

For a pure bundle test, no arguments should be provided. This way, the bundle
yaml is rendered with default values (all charms deployed from charmhub).

```shell
tox -e integration
```


To keep the model and applications running after the tests completes:

```shell
tox -e integration -- --keep-models
```

To run the end-to-end tests, you first need to have a k8s and a lxd controllers
bootstrapped, and communicate their names using environment variables:
```shell
K8S_CONTROLLER="k8s_ctl_name" LXD_CONTROLLER="lxd_ctl_name" tox -e e2e
```

### Tests with local charms
To have all charms deployed from local files, first render the bundle and then
run integration tests.

```shell
./render_bundle.py bundle.yaml --channel=edge \
  --traefik=$(pwd)/../traefik-k8s-operator/traefik-k8s_ubuntu-20.04-amd64.charm \
  --prometheus=$(pwd)/../prometheus-k8s-operator/prometheus-k8s_ubuntu-20.04-amd64.charm \
  --alertmanager=$(pwd)/../alertmanager-k8s-operator/alertmanager-k8s_ubuntu-20.04-amd64.charm \
  --grafana=$(pwd)/../grafana-k8s-operator/grafana-k8s_ubuntu-20.04-amd64.charm \
  --loki=$(pwd)/../loki-operator/loki-k8s-operator_ubuntu-20.04-amd64.charm

tox -e integration
```

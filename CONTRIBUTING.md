# Overview

This documents explains the processes and practices recommended for
contributing enhancements to the LMA Light bundle.

- Generally, before developing enhancements to this charm, you should consider
  [opening an issue](https://github.com/canonical/lma-light-bundle) explaining
  your use case.
- If you would like to chat with us about your use cases or proposed
  implementation, you can reach us on the
  [Charmhub Mattermost](https://chat.charmhub.io/charmhub/channels/charm-dev)
  or [Discourse](https://discourse.charmhub.io/).
- All enhancements require review before being merged.
  Apart from code quality and test coverage, the review will also take into
  account the Juju administrator user experience using the bundle.

## Development

### Deploy from a local bundle file

```shell
juju deploy ./bundle.yaml
```

### Deploy with local charms

```shell
juju deploy ./bundle-local.yaml
```

## Testing
Integration tests can be run with
```shell
tox -e integration
```

To keep the model and applications running after the tests completed,
```shell
tox -e integration -- --keep-models
```

### Manual tests
Integration tests expect to have a `bundle-testing.yaml` file present, which
can be rendered by passing arguments to the `render` environment.

For a pure bundle test, no arguments should be provided. This way, the bundle
yaml is rendered with default values (all charms deployed from charmhub).
```shell
# render with defaults (all charms deployed from charmhub)
tox -e render
```

For manual/local tests, paths to local charms can be passed to tox, which in
turn are passed on to the [`render_bundle.py`](render_bundle.py) script.
For example, to render a bundle with a local prometheus charm but all the other
charms taken from charmhub,
```shell
tox -e render -- --prometheus=./../prometheus-operator/prometheus-k8s_ubuntu-20.04-amd64.charm
```

Or to have all charms deployed from local files:
```shell
tox -e render -- --prometheus=./../prometheus-operator/prometheus-k8s_ubuntu-20.04-amd64.charm \
  --alertmanager=./../alertmanager-operator/alertmanager-k8s_ubuntu-20.04-amd64.charm \
  --grafana=./../grafana-operator/grafana-k8s_ubuntu-20.04-amd64.charm \
  --tester=./../prometheus-tester/prometheus-tester_ubuntu-20.04-amd64.charm
```

After a `bundle-testing.yaml` file is rendered, integration tests can be run
with:
```shell
tox -e rendered-integration
```

Please refer to the
[project page on GitHub](https://github.com/canonical/lma-light-bundle)
for further details.

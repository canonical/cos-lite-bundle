# LMA light bundle
This bundle deploys a light LMA stack with the following interrelated charms:
- [grafana](https://charmhub.io/grafana-k8s) ([source](https://github.com/canonical/grafana-operator))
- [prometheus](https://charmhub.io/prometheus-k8s) ([source](https://github.com/canonical/prometheus-operator))
- [alertmanager](https://charmhub.io/alertmanager-k8s) ([source](https://github.com/canonical/alertmanager-operator))

## Usage
Before deploying the bundle you may want to create a dedicated model for it:

```shell
juju add-model lma
juju switch lma
```

You can deploy the bundle with:

```shell
juju deploy lma-light
```

## Development
### Local bundle
```shell
juju deploy ./bundle.yaml
```

### Local bundle, using local charms
```shell
juju deploy ./bundle-local.yaml
```

Please refer to the [project page on github](https://github.com/sed-i/lma-light-bundle) for further details.

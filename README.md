# COS Lite bundle

Canonical Observability Stack Lite, or COS Lite, is a light-weight, highly-integrated, Juju-based observability suite running on Kubernetes. 
This Juju bundle deploys the stack, consisting of the following interrelated charms:

- [Prometheus](https://charmhub.io/prometheus-k8s) ([source](https://github.com/canonical/prometheus-operator))
- [Loki](https://charmhub.io/loki-k8s) ([source](https://github.com/canonical/loki-operator))
- [Alertmanager](https://charmhub.io/alertmanager-k8s) ([source](https://github.com/canonical/alertmanager-operator))
- [Grafana](https://charmhub.io/grafana-k8s) ([source](https://github.com/canonical/grafana-operator))

This bundle is under development.
Join us on [Discourse](https://discourse.charmhub.io/t/canonical-observability-stack/5132) and [MatterMost](https://chat.charmhub.io/charmhub/channels/observability)!

## The Vision

COS Lite is going to be the go-to solution for monitoring Canonical appliances when the end user does not already have an established observability stack.
COS Lite is designed for:

* Best-in-class monitoring of software [charmed with Juju](https://juju.is)
* Limited resource consumption
* High integration and out-of-the-box value
* Running on [MicroK8s](https://microk8s.io/)

After the GA of COS Lite, we will be working on a High-Availability Bundle (COS HA), that will use the same components as COS Lite (plus additional ones) and provide the same overall user-experience, and focus on scalability, resilience and broad compatibility with Kubernetes distributions out there.

## Usage

Before deploying the bundle you may want to create a dedicated model for it:

```shell
juju add-model cos
juju switch cos
```

You can deploy the bundle from charmhub with:

```shell
juju deploy cos-lite --channel=edge --trust
```

or, to deploy the bundle from a local file:

```shell
# generate and activate a virtual environment with dependencies
tox -e integration --notest
source .tox/integration/bin/activate

# render bundle with default values
./render_bundle.py bundle.yaml
juju deploy ./bundle.yaml --trust
```

Currently the bundle is available only on the `edge` channel, using `edge` charms.
When the charms graduate to `beta`, `candidate` and `stable`, we will issue the bundle in the same channels.

The `--trust` option is needed by the charms in the `cos-lite` bundle to be able to patch their K8s services to use the right ports (see this [Juju limitation](https://bugs.launchpad.net/juju/+bug/1936260)).

We also make available some [**overlays**](https://juju.is/docs/sdk/bundle-reference) as convenience.
A Juju overlay is a set of model-specific modifications, which reduce the amount of commands needed to set up a bundle like COS Lite.
Specifically, we offer the following overlays:

* the [`offers` overlay](https://raw.githubusercontent.com/canonical/cos-lite-bundle/main/overlays/offers-overlay.yaml) exposes as offers the relation endpoints of the COS Lite charms that are likely to be consumed over [cross-model relations](https://juju.is/docs/olm/cross-model-relations).
* the [`storage-small` overlays](https://raw.githubusercontent.com/canonical/cos-lite-bundle/main/overlays/storage-small-overlay.yaml) provides a setup of the various storages for the COS Lite charms for a small setup.
  Using an overlay for storage is fundamental for a productive setup, as you cannot change the amount of storage assigned to the various charms after the deployment of COS Lite.

In order to use the overlays above, you need to:

1. Download the overlays (or clone the repository)
2. Pass the `--overlay <path-to-overlay-file-1> --overlay <path-to-overlay-file-2> ...` arguments to the `juju deploy` command

For example, to deploy the COS Lite bundle with the offers overlay, you would do the following:

```sh
curl -L https://raw.githubusercontent.com/canonical/cos-lite-bundle/main/overlays/offers-overlay.yaml -O

juju deploy cos-lite --channel=edge --trust --overlay ./offers-overlay.yaml
```

## Publishing
```shell
./render_bundle.py bundle.yaml --channel=edge
charmcraft pack
charmcraft upload cos-lite.zip
charmcraft release cos-lite --channel=beta --revision=4
```

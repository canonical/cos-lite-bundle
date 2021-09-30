# LMA Light bundle

At Canonical, LMA stands for "Logs, Metrics and Alerts", and is a moniker to describe observability stacks.
This Juju bundle deploys such an observability stack, called "LMA Light", based on consisting of the following interrelated charms:

- [Prometheus](https://charmhub.io/prometheus-k8s) ([source](https://github.com/canonical/prometheus-operator))
- [Loki](https://charmhub.io/loki-k8s) ([source](https://github.com/canonical/loki-operator))
- [Alertmanager](https://charmhub.io/alertmanager-k8s) ([source](https://github.com/canonical/alertmanager-operator))
- [Grafana](https://charmhub.io/grafana-k8s) ([source](https://github.com/canonical/grafana-operator))

This bundle is very much work in progress.
For example, there is currently no "L" in LMA, i.e., there is no logging component integrated yet, there are several administrative use-cases to support, and more.

## The Vision

LMA Light is going to be the go-to solution for monitoring Canonical appliances when the end user does not already have an established observability stack.
LMA Light is designed for:

* Best-in-class monitoring of software [charmed with Juju](https://juju.is)
* Limited resource consumption
* High integration and out-of-the-box value
* Running on [MicroK8s](https://microk8s.io/)

After the GA of LMA Light, we will be working on a High-Availability Bundle (LMA HA), that will use the same components as LMA Light (plus additional ones) and provide the same overall user-experience, and focus on scalability, resilience and broad compatibility with Kubernetes distributions out there.

## Usage

Before deploying the bundle you may want to create a dedicated model for it:

```shell
juju add-model lma
juju switch lma
```

You can deploy the bundle from charmhub with:

```shell
juju deploy lma-light --channel=edge --trust
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

The `--trust` option is needed by the charms in the `lma-light` bundle to be able to patch their K8s services to use the right ports (see this [Juju limitation](https://bugs.launchpad.net/juju/+bug/1936260)).

We also make available some [**overlays**](https://juju.is/docs/sdk/bundle-reference) as convenience.
A Juju overlay is a set of model-specific modifications, which reduce the amount of commands needed to set up a bundle like LMA Light.
Specifically, we offer the following overlays:

* the [`offers` overlay](./overlays/offers-overlay.yaml) exposes as offers the relation endpoints of the LMA Light charms that are likely to be consumed over [cross-model relations](https://juju.is/docs/olm/cross-model-relations).
* the [`storage-small` overlays](./overlays/storage-small-overlay.yaml) provides a setup of the various storages for the LMA Light charms for a small setup.
  Using an overlay for storage is fundamental for a productive setup, as you cannot change the amount of storage assigned to the various charms after the deployment of LMA Light.

In order to use the overlays above, you need to:

1. Download the overlays (or clone the repository)
2. Pass the `--overlay <path-to-overlay-file-1> --overlay <path-to-overlay-file-2> ...` arguments to the `juju deploy` command

For example, to deploy the LMA Light bundle with the offers overlay, you would do the following:

```sh
curl -L https://github.com/canonical/lma-light-bundle/blob/main/overlays/offer-overlay.yaml -O

juju deploy lma-light --channel=edge --overlay ./offers-overlay.yaml
```

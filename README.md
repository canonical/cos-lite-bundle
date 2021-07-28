# LMA Light bundle

At Canonical, LMA stands for "Logs, Metrics and Alerts", and is a moniker to describe observability stacks.
This Juju bundle deploys such an observability stack, called "LMA Light", based on consisting of the following interrelated charms:

- [Grafana](https://charmhub.io/grafana-k8s) ([source](https://github.com/canonical/grafana-operator))
- [Prometheus](https://charmhub.io/prometheus-k8s) ([source](https://github.com/canonical/prometheus-operator))
- [Alertmanager](https://charmhub.io/alertmanager-k8s) ([source](https://github.com/canonical/alertmanager-operator))

This bundle is very much work in progress.
For example, there is currently no "L" in LMA, i.e., there is no logging component integrated yet, there are several administrative use-cases to support, and more.

## The Vision

LMA Light is going to be the go-to solution for monitoring Canonical appliance when the end user does not already have an established observability stack.
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

You can deploy the bundle with:

```shell
juju deploy lma-light
```

# Manual tests

## 3-node cluster in a multipass VM (nested virtualization)
The [`microk8s-ha.yaml`](microk8s-ha.yaml) file contains a cloud-init script
for an "all in one" VM. When launched the VM will have three nested VMs called
"node-1", "node-2" and "node-3".

```mermaid
graph LR

subgraph microk8s-ha multipass VM

subgraph node-0 multipass VM
microk8s_0[microk8s]
end

subgraph node-1 multipass VM
microk8s_1[microk8s]
end

subgraph node-2 multipass VM
microk8s_2[microk8s]
end

juju

end
```

Launch the VM with:
```bash
multipass launch 22.04 --cloud-init microk8s-ha.yaml \
  --timeout 1800 \
  --name three-node \
  --memory 16G \
  --cpus 14 \
  --disk 100G
```

Then shell into the vm, get the `three-nodes-overlay.yaml` file and run:
```bash
juju deploy --trust cos-lite --overlay ./three-nodes-overlay.yaml
```

From within the "outer VM" you can `multipass exec` into the node VMs:
```bash
multipass exec node-1 microk8s.kubectl -n welcome-k8s get pods -A
```

Note that with Juju <3.3.5,<3.4.4, you would need to manually patch the
statefulsets due to a [bug](https://bugs.launchpad.net/juju/+bug/2062934).

## CMR to Ceph with Grafana-agent
The `lxd-ceph-cmr.yaml` file contains a bundle for deploying Ceph with grafana-agent (subordinate) on a LXD model. This bundle expects a CMR to a COS-lite deployment in microk8s which can be created by running `juju deploy cos-lite --trust --overlay ./offers-overlay.yaml`.

Validation Process
1. Open the Grafana UI with:
`juju run traefik/0 show-proxied-endpoints --format=yaml | yq '."traefik/0".results."proxied-endpoints"' | jq`
`juju run grafana/leader get-admin-password`
2. Navigate to `Home/Dashboards` and check that Ceph dashboards exist and have populated data.
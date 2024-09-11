#!/bin/bash

juju ssh alertmanager/0 cat agents/unit-alertmanager-0/charm/src/grafana_dashboards/alertmanager_rev4.json.tmpl | jq -r '.uid'
juju ssh --container grafana grafana/0 ls /etc/grafana/provisioning/dashboards/

# Collect all the UIDs from the charm using  and make sure it is a subset of the UIDs in Grafana
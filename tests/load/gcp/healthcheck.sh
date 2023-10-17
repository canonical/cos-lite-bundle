#!/usr/bin/env bash

# This script is intended to run on the same host that used to provision the VMs with terraform.

VM_COS_IP=$(terraform output -json | jq -r '.ip_nat_vm_cos_lite_appliance.value')
PROM_INTERNAL_URL=$(terraform output -json | jq -r '.prom_internal_url.value')


check_prom_ready() {
  echo "==="
  echo "Checking prometheus..."
  ssh -i ~/secrets/cos-lite-load-testing-ssh -o "UserKnownHostsFile=/dev/null" -o "StrictHostKeyChecking no" "ubuntu@$VM_COS_IP" curl -s "$PROM_INTERNAL_URL/-/ready" 2>/dev/null
  echo "---"
  echo "Number of scrape targets:"
  ssh -i ~/secrets/cos-lite-load-testing-ssh -o "UserKnownHostsFile=/dev/null" -o "StrictHostKeyChecking no" "ubuntu@$VM_COS_IP" curl -s "$PROM_INTERNAL_URL/api/v1/targets" 2>/dev/null | jq ".data.activeTargets[].scrapeUrl" | wc -l
  echo "==="
}

check_grafana_password() {
  echo "==="
  echo "Checking grafana password..."
  ssh -i ~/secrets/cos-lite-load-testing-ssh -o "UserKnownHostsFile=/dev/null" -o "StrictHostKeyChecking no" "ubuntu@$VM_COS_IP" curl localhost:8081/helper/grafana/password 2>/dev/null
  echo
  echo "==="
}

check_prom_ready
check_grafana_password

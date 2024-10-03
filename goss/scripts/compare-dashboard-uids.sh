#!/bin/sh

# Collect the UID from the charm dashboard and check if it is a subset of Grafana dashboard UIDs

MODEL_NAME="$1"
GRAFANA_APP_NAME="$2"
OTHER_APP_NAME="$3"
GRAFANA_DASHBOARD_DIR="/etc/${GRAFANA_APP_NAME}/provisioning/dashboards/"
OTHER_APP_DASHBOARD_DIR="agents/unit-${OTHER_APP_NAME}-0/charm/src/grafana_dashboards/"
TARGET_UID=$(juju ssh ${OTHER_APP_NAME}/0 "cat ${OTHER_APP_DASHBOARD_DIR}/${OTHER_APP_NAME}*.json.tmpl" | jq -r '.uid')

# Get the list of JSON files in the Grafana dashboard directory inside the workload container
file_list=$(juju ssh -m ${MODEL_NAME} --container grafana ${GRAFANA_APP_NAME}/0 "ls ${GRAFANA_DASHBOARD_DIR}*.json")
match_found=false

# Iterate over each dashboard file
for file_path in ${file_list}; do

  # Get the contents of each dashboard and use jq to extract the 'uid'
  uid=$(juju ssh -m ${MODEL_NAME} --container grafana ${GRAFANA_APP_NAME}/0 "cat ${file_path}" | jq -r '.uid')

  # Check if UID extraction was successful
  if [ -n "$uid" ]; then
    if [ "$uid" == "$TARGET_UID" ]; then
      match_found=true
      break  # Exit the loop early since a match was found
    fi
  fi
done

if [ "$match_found" = true ]; then
  echo "Match found."
else
  echo "The ${OTHER_APP_NAME} dashboard UID is not a subset of the Grafana dashboard UIDs."
fi
#!/bin/bash

# Collect all the UIDs from the charm using  and make sure it is a subset of the UIDs in Grafana
# juju ssh alertmanager/0 cat agents/unit-alertmanager-0/charm/src/grafana_dashboards/alertmanager_rev4.json.tmpl | jq -r '.uid'
# juju ssh --container grafana grafana/0 ls /etc/grafana/provisioning/dashboards/

# Define the path to the directory containing the dashboard files
GRAFANA_APP_NAME="$1"
OTHER_APP_NAME="$2"
CHARM_DASHBOARD_DIR="agents/unit-${OTHER_APP_NAME}-0/charm/src/grafana_dashboards/"
GRAFANA_DASHBOARD_DIR="/etc/${GRAFANA_APP_NAME}/provisioning/dashboards/"

# Loop through each file in the directory
juju ssh --container ${GRAFANA_APP_NAME} ${GRAFANA_APP_NAME}/0 "for file in ${GRAFANA_DASHBOARD_DIR}*.json; do
  echo $file
  # Extract the UID using jq
  uid=\$(jq -r '.uid' \"\$file\" 2>/dev/null)
  
  # Check if UID extraction was successful
  if [ -n \"\$uid\" ]; then
    # Compare the extracted UID with the target UID
    if [ \"\$uid\" == \"$TARGET_UID\" ]; then
      echo \"Match found in: \$file\"
    else
      echo \"UID in \$file does not match\"
    fi
  else
    echo \"Failed to extract UID or not a JSON file: \$file\"
  fi
done"

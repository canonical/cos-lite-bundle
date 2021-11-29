#!/bin/bash
set -euxo pipefail

apt update && apt install -y python3-pip jq && python3 -m pip install locust

# wait until the lma node is up
until curl -s --connect-timeout 2.0 ${PROM_URL}/api/v1/targets; do sleep 5; done

# without piping to jq, curl would return successfully with "nginx 404 not found"
until (( $(sh -c "curl -s --connect-timeout 2.0 ${PROM_URL}/api/v1/targets | jq '.data.activeTargets[].health' 2>/dev/null | wc -l") > 1 )); do sleep 5; done

# now that prom is really reachable, start locust
python3 -m locust -f /home/ubuntu/prom-query-locustfile.py --host ${PROM_URL} --users 1 --spawn-rate 1 --headless


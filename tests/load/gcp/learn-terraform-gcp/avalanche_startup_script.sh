#!/bin/bash
for ((i = 1 ; i <= 20 ; i++)) ; do port=$((9000 + $i)); `nohup avalanche --metric-count=1000 --label-count=10 --series-count=10 --value-interval=30 --series-interval=36000000 --metric-interval=36000000 --port=$port 1>/dev/null 2>&1 &` ; done


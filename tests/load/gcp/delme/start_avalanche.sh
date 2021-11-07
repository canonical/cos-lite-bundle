#!/bin/bash -e

# $1 = num of instances
if [ "$#" -ne 1 ]; then
    num=1
else
    num=$1
fi

echo "Num: $num"

for ((i = 1 ; i <= $num ; i++)); do
    port=$((9000 + $i))
    nohup ./cmd --metric-count=25000 --label-count=10 --series-count=10 --value-interval=30 --series-interval=3600000 --metric-interval=3600000 --port=$port 1>/dev/null 2>&1 &
done;


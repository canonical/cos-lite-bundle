#!/usr/bin/env bash

ZONE="us-central1-a"
PROJECT="lma-light-load-testing"
CREATE="gcloud compute instances create --project=$PROJECT --zone=$ZONE --network-interface=network-tier=PREMIUM,subnet=default --maintenance-policy=MIGRATE --service-account=921396806154-compute@developer.gserviceaccount.com --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append --no-shielded-secure-boot --shielded-vtpm --shielded-integrity-monitoring --reservation-affinity=any"
START="gcloud compute instances start --project=$PROJECT --zone=$ZONE"
SSH="gcloud compute ssh --project $PROJECT --zone $ZONE"

# LMA spec
NCPU=2
GBMEM=4
INSTANCE="n1-ssd-${NCPU}cpu-${GBMEM}gb"  # e.g. n1-ssd-2cpu-8gb
AVALANCHE_INSTANCE="avalanche-$INSTANCE"  # e.g. avalanche-n1-ssd-2cpu-8gb
URL_LMA="$INSTANCE.$ZONE.c.$PROJECT.internal"  # e.g. n1-ssd-2cpu-8gb.c.lma-light-load-testing.internal
URL_AVALANCHE="$AVALANCHE_INSTANCE.$ZONE.c.$PROJECT.internal"  # e.g. avalanche-n1-ssd-2cpu-8gb.c.lma-light-load-testing.internal

start_avalanche () {
  if [[ $(gcloud compute instances describe "${AVALANCHE_INSTANCE}") ]]; then
    echo "avalanche instance ${AVALANCHE_INSTANCE} already exists"
    gcloud compute instances stop "${AVALANCHE_INSTANCE}"
  else
    echo "Creating avalanche instance ${AVALANCHE_INSTANCE}"
    $CREATE "${AVALANCHE_INSTANCE}" --machine-type=e2-standard-4 --create-disk=auto-delete=yes,boot=yes,device-name=disk-"${AVALANCHE_INSTANCE}",image=projects/lma-light-load-testing/global/images/avalanche,mode=rw,size=10,type=projects/lma-light-load-testing/zones/us-central1-a/diskTypes/pd-balanced
  fi

  echo "Starting avalanche instance..."
  $START "${AVALANCHE_INSTANCE}"
  sleep 60
  echo "Starting avalanche workers..."
  $SSH "${AVALANCHE_INSTANCE}" -- 'for ((i = 1 ; i <= 20 ; i++)) ; do port=$((9000 + $i)); `nohup avalanche --metric-count=1000 --label-count=10 --series-count=10 --value-interval=30 --series-interval=36000000 --metric-interval=36000000 --port=$port 1>/dev/null 2>&1 &` ; done'
}

start_lma () {
  # $1 = number of avalanche targets to scrape
  NUM_SCRAPE_TARGETS=$1

  # create SSD instance
  echo "Creating $INSTANCE..."
  $CREATE $INSTANCE --machine-type=custom-${NCPU}-$(( GBMEM * 1024 )) --create-disk=auto-delete=yes,boot=yes,device-name=disk-${INSTANCE},image=projects/lma-light-load-testing/global/images/juju-hirsute-dns-ingress,mode=rw,size=50,type=projects/lma-light-load-testing/zones/us-central1-a/diskTypes/pd-ssd

  # start instance
  echo "Starting $INSTANCE..."
  gcloud compute instances start $INSTANCE --project=$PROJECT --zone=$ZONE
  sleep 30

  # test comms with avalanche
  echo "Testing comms with ${URL_AVALANCHE}..."
  $SSH $INSTANCE --command=<<EOF
curl http://${URL_AVALANCHE}:9001/metrics | wc -l
curl http://${URL_AVALANCHE}:9002/metrics | wc -l
EOF

  # add current user to group
  echo "Adding $USER to the microk8s group..."
  $SSH $INSTANCE --command=<<EOF
sudo usermod -a -G microk8s $USER
sudo chown -f -R $USER ~/.kube
EOF

  SCRAPE_TARGETS="${URL_AVALANCHE}:9001"
  for ((i = 2 ; i <= NUM_SCRAPE_TARGETS ; i++)) ; do SCRAPE_TARGETS="${SCRAPE_TARGETS},${URL_AVALANCHE}:$((9000 + $i))"; done

  # deploy lma-light bundle
  echo "Deploying lma-light..."
  $SSH $INSTANCE --command=<<EOF
sudo systemctl start snap.microk8s.daemon-containerd
sudo systemctl start snap.microk8s.daemon-kubelite
sudo snap alias microk8s.kubectl kubectl
sudo snap alias microk8s.kubectl k
sleep 30
microk8s.status --wait-ready
microk8s inspect
until microk8s.kubectl rollout status deployments/hostpath-provisioner -n kube-system -w; do sleep 5; done
until microk8s.kubectl rollout status deployments/coredns -n kube-system -w; do sleep 5; done

IPADDR=\$(ip -4 route | grep default | grep -oP 'src \K\S+')
microk8s.enable metallb:\${IPADDR}-\${IPADDR}

juju status
sleep 60
juju bootstrap microk8s lma-ctrlr
juju add-model lma --config logging-config='<root>=WARNING; unit=DEBUG' --config update-status-hook-interval=60m
juju deploy --channel=edge lma-light --trust
juju deploy --channel=edge --trust prometheus-scrape-target-k8s scrape-target --config targets=${SCRAPE_TARGETS}
juju deploy --channel=edge --trust prometheus-scrape-config-k8s scrape-config --config scrape-interval=60s --config scrape-timeout=55s
juju relate scrape-config:configurable-scrape-jobs scrape-target:metrics-endpoint
juju relate scrape-config:metrics-endpoint prometheus:metrics-endpoint
juju status --relations

microk8s.kubectl apply -f - <<'EOY'
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: prom-ingress
  namespace: lma
  annotations:
    nginx.ingress.kubernetes.io/use-regex: "true"
    nginx.ingress.kubernetes.io/rewrite-target: /\$1
spec:
  ingressClassName: public
  rules:
  - http:
      paths:
      - path: /prom/(.*)
        pathType: Prefix
        backend:
          service:
            name: prometheus
            port:
              number: 9090
      - path: /loki/(.*)
        pathType: Prefix
        backend:
          service:
            name: loki
            port:
              number: 3100
EOY
EOF
}

start_avalanche
start_lma 1

# locust -f prom-query-locustfile.py --host http://n1-ssd-2cpu-4gb.c.lma-light-load-testing.internal/prom --users 1 --spawn-rate 1 --headless

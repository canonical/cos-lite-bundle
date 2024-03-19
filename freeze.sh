#!/usr/bin/env bash
# This script generates a revision manifest for COS charms.

# Usage example:
# ./freeze.sh latest/stable amd64 | jq -s add > freeze/bundle_stable_amd64.json

set -euo pipefail

if [[ $# -ne 2 ]]; then
  # $1 = channel, e.g. latest/edge
  # $2 = base architecture, e.g. amd64
  echo "Usage: $0 <channel> <base_arch>"
  echo "Example: $0 latest/edge amd64"
  exit 1
fi

# CHARMHUB_TOKEN has the same semantics as in charming-actions: credentials exported using
# `charmcraft login --export`.
# https://github.com/canonical/charming-actions/tree/main/release-charm

if [[ -z "${CHARMHUB_TOKEN}" ]]; then
  # CHARMHUB_TOKEN is not set. Try the CREDS_FILE
  CREDS_FILE="charmhub-creds.dat"

  if [ ! -e "$CREDS_FILE" ]; then
    echo "Error: Credentials file $CREDS_FILE does not exist and environment variable"
    echo "       CHARMHUB_TOKEN is not set."
    echo
    echo "Before running this script, first login with charmhub:"
    echo "  charmcraft login --export $CREDS_FILE"
    echo "or set the CHARMHUB_TOKEN variable."
    exit 1
  fi
  CHARMHUB_MACAROON_HEADER="Authorization: Macaroon $(base64 -d $CREDS_FILE | jq -r .v)"
else
  # CHARMHUB_TOKEN is set, so takes precedence over CREDS_FILE
  CHARMHUB_MACAROON_HEADER="Authorization: Macaroon $(echo "$CHARMHUB_TOKEN" | base64 -d | jq -r .v)"
fi

get_charm_revisions () {
  # $1 = charm name, e.g. grafana-k8s
  # $2 = channel, e.g. latest/edge
  # $3 = base architecture, e.g. amd64
  # $4 = base channel, e.g. 20.04

  if [[ $# -ne 4 ]]; then
    echo "Usage: get_charm_revisions <charm> <channel> <base_arch> <base_channel>"
    return 1
  fi

  curl -s -H'Content-type: application/json' \
    -H "$CHARMHUB_MACAROON_HEADER" \
    "https://api.charmhub.io/v1/charm/$1/releases" \
    | jq '."channel-map" | .[]' \
    | jq "select(.channel == \"$2\")" \
    | jq "select(.base.architecture == \"$3\")" \
    | jq "select(.base.channel == \"$4\")" \
    | jq '{revision, resources: (.resources | map({(.name): (.revision)}) | add)}' \
    | jq "{\"$1\": .}"

  # Output looks like this:
  # {
  #   "grafana-k8s": {
  #     "revision": 106,
  #     "resources": {
  #       "grafana-image": 68,
  #       "litestream-image": 43
  #     }
  #   }
  # }
}


CHANNEL="latest/stable"
BASE_ARCH="amd64"

get_charm_revisions "grafana-agent-k8s" "$CHANNEL" "$BASE_ARCH" "22.04"
get_charm_revisions "traefik-k8s" "$CHANNEL" "$BASE_ARCH" "20.04"
get_charm_revisions "catalogue-k8s" "$CHANNEL" "$BASE_ARCH" "20.04"
get_charm_revisions "grafana-k8s" "$CHANNEL" "$BASE_ARCH" "20.04"
get_charm_revisions "loki-k8s" "$CHANNEL" "$BASE_ARCH" "20.04"
get_charm_revisions "prometheus-k8s" "$CHANNEL" "$BASE_ARCH" "20.04"
get_charm_revisions "alertmanager-k8s" "$CHANNEL" "$BASE_ARCH" "20.04"


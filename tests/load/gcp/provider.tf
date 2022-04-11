terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "4.41.0"
    }
  }
}

provider "google" {
  credentials = local.gcp_credentials

  project = var.project
  region  = var.region
  zone    = var.zone
}

resource "google_compute_network" "net_cos_lite_load_test_net" {
  name = "cos-lite-load-test-net"
}

resource "google_compute_firewall" "internal_all_to_all" {
  name    = "internal-all-to-all"
  network = google_compute_network.net_cos_lite_load_test_net.name

  allow {
    protocol = "icmp"
  }

  allow {
    protocol = "tcp"
    ports    = ["22", "80"]
  }

  target_tags = ["load-test-traffic"]
  source_tags = ["load-test-traffic"]
}

resource "google_compute_firewall" "internal_scrape_targets" {
  name    = "internal-scrape-targets"
  network = google_compute_network.net_cos_lite_load_test_net.name

  allow {
    protocol = "tcp"
    ports    = ["9001-${9000 + var.num_avalanche_targets}"]
  }

  target_tags = ["vm-prom-scrape"]
  source_tags = ["load-test-traffic"]
}

resource "google_compute_firewall" "internal_appliance_helper" {
  # Expose port 8081, where the helper webserver serves the grafana password, and potentially more
  # things in the future, if the need arises.
  name    = "internal-appliance-helper"
  network = google_compute_network.net_cos_lite_load_test_net.name

  allow {
    protocol = "tcp"
    ports    = ["8081"]
  }

  target_tags = ["vm-cos-lite-appliance"]
  source_tags = ["load-test-traffic"]
}

data "http" "myip" {
  url = "http://ipv4.icanhazip.com"
}

resource "google_compute_firewall" "external_scrape" {
  # Port 29100: for scraping node-exporter from the terraform host machine.
  # Port 80: for self /metrics endpoints from ingressed subpaths.
  name    = "external-scrape"
  network = google_compute_network.net_cos_lite_load_test_net.name

  allow {
    protocol = "tcp"
    ports    = ["29100", "80"]
  }

  target_tags   = ["load-test-traffic"]
  #source_ranges = ["${chomp(data.http.myip.response_body)}/32"]
  source_tags = ["vm-monitoring"]
}


resource "google_compute_firewall" "ssh" {
  # For ssh-ing into VMs from the terraform host machine.
  name    = "ssh"
  network = google_compute_network.net_cos_lite_load_test_net.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  target_tags = ["load-test-traffic"]
  # source_ranges = ["${chomp(data.http.myip.response_body)}/32"]
  source_ranges = ["0.0.0.0/0"]
}

locals {
  ssh_public_key  = file(pathexpand("~/secrets/cos-lite-load-testing-ssh.pub"))
  ssh_private_key = file(pathexpand("~/secrets/cos-lite-load-testing-ssh"))

  # The JSON key file for editing GCP resources
  gcp_credentials = file(pathexpand("~/secrets/cos-lite-load-testing-e767258f9d07.json"))

  ssh_keys = <<EOF
    ubuntu:${local.ssh_public_key}
  EOF
}

resource "google_compute_project_metadata" "gcp_metadata" {
  metadata = {
    ssh-keys = local.ssh_keys
  }
}


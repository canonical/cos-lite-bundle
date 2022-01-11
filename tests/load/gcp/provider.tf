terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "3.5.0"
    }
  }
}

provider "google" {
  credentials = file(var.credentials_file)

  project = var.project
  region  = var.region
  zone    = var.zone
}

resource "google_compute_network" "net_lma_light_load_test_net" {
  name = "lma-light-load-test-net"
}

resource "google_compute_firewall" "internal_all_to_all" {
  name    = "internal-all-to-all"
  network = google_compute_network.net_lma_light_load_test_net.name

  allow {
    protocol = "icmp"
  }

  allow {
    protocol = "tcp"
    ports    = ["22", "80", "9001-${9000 + var.num_avalanche_targets}", "9090"]
  }

  target_tags = ["load-test-traffic"]
  source_tags = ["load-test-traffic"]
}

data "http" "myip" {
  url = "http://ipv4.icanhazip.com"
}

resource "google_compute_firewall" "external_scrape" {
  # For scraping node-exporter from the terraform host machine.
  name    = "external-scrape"
  network = google_compute_network.net_lma_light_load_test_net.name

  allow {
    protocol = "tcp"
    ports    = ["9100"]
  }

  target_tags   = ["vm-lma-appliance"]
  source_ranges = ["${chomp(data.http.myip.body)}/32"]
}


resource "google_compute_firewall" "ssh" {
  # For ssh-ing into VMs from the terraform host machine.
  name    = "ssh"
  network = google_compute_network.net_lma_light_load_test_net.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  target_tags   = ["load-test-traffic"]
  source_ranges = ["${chomp(data.http.myip.body)}/32"]
}

locals {
  ssh_keys = <<EOF
    ubuntu:${file(var.ssh_key_public_path)}
  EOF
}

resource "google_compute_project_metadata" "gcp_metadata" {
  metadata = {
    ssh-keys = local.ssh_keys
  }
}


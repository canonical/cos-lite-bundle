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

resource "google_compute_firewall" "load_test_traffic" {
  name    = "load-test-traffic"
  network = google_compute_network.net_lma_light_load_test_net.name

  allow {
    protocol = "tcp"
    ports    = ["22", "80", "9001-9100", "9090"]
  }

  allow {
    protocol = "icmp"
  }

  target_tags   = ["load-test-traffic"]
  source_ranges = ["0.0.0.0/0"]
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


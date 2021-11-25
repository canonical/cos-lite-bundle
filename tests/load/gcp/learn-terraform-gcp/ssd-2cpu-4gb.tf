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

resource "google_compute_firewall" "ssh-rule" {
  name = "demo-ssh"
  network = google_compute_network.net_lma_light_load_test_net.name
  allow {
    protocol = "tcp"
    ports = ["22"]
  }
  target_tags = ["ssd-2cpu-8gb"]
  source_ranges = ["0.0.0.0/0"]
}

resource "google_compute_instance" "vm_ssd_2cpu_8gb" {
  name         = "ssd-2cpu-8gb"
  machine_type = "custom-4-8192"
  tags         = ["ssd-2cpu-8gb"]

  boot_disk {
    initialize_params {
      image = "projects/lma-light-load-testing/global/images/juju-hirsute-dns-ingress"
      type  = "pd-ssd"
      size  = "50"
    }
  
  }

  metadata_startup_script = file(var.lma_startup_script)

  network_interface {
    network = google_compute_network.net_lma_light_load_test_net.name

    access_config {
    }
  }
}

resource "google_compute_instance" "vm_avalanche_for_ssd_2cpu_8gb" {
  name         = "avalanche-for-ssd-2cpu-8gb"
  machine_type = "e2-standard-4"

  boot_disk {
    initialize_params {
      image = "projects/lma-light-load-testing/global/images/avalanche"
    }
  }

  network_interface {
    network = google_compute_network.net_lma_light_load_test_net.name

    access_config {
    }
  }
}



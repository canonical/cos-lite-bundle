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

resource "google_compute_project_metadata" "my_ssh_key" {
  metadata = {
    # ssh-keygen -t rsa -b 4096 -f ~/secrets/lma-light-load-testing-ssh -C "" 
    ssh-keys = <<EOF
      ubuntu:${file("~/secrets/lma-light-load-testing-ssh.pub")}
    EOF
  }
}


locals {
  # ncpus = 4
  # gbmem = 8
  instance_name = "ssd-${var.ncpus}cpu-${var.gbmem}gb"
  machine_type = "custom-${var.ncpus}-${var.gbmem * 1024}"
}

resource "google_compute_instance" "vm_lma_appliance" {
  name         = local.instance_name
  machine_type = local.machine_type
  tags         = ["load-test-traffic"]

  boot_disk {
    initialize_params {
      image = "projects/lma-light-load-testing/global/images/juju-hirsute-dns-ingress"
      type  = var.disk_type
      size  = "50"
    }
  }

  provisioner "file" {
    # AVALANCHE_URL: e.g. avalanche-n1-ssd-2cpu-8gb.c.lma-light-load-testing.internal
    content      = templatefile("overlay-load-test.tpl.yaml", { AVALANCHE_URL = "${google_compute_instance.vm_avalanche_for_ssd_2cpu_8gb.name}.${var.zone}.c.${var.project}.internal", PORTS = var.avalanche_ports })
    destination = var.overlay_load_test
    
    connection {
      type = "ssh"
      user = "ubuntu"
      #host = self.network_interface[0].access_config[0].nat_ip
      host        = google_compute_instance.vm_lma_appliance.network_interface.0.access_config.0.nat_ip
      private_key = file("~/secrets/lma-light-load-testing-ssh")
      #agent = "false"
    }
  }

  metadata_startup_script = templatefile(var.lma_startup_script, { OVERLAY_LOAD_TEST = var.overlay_load_test })

  network_interface {
    network = google_compute_network.net_lma_light_load_test_net.name

    access_config {
    }
  }
}

resource "google_compute_instance" "vm_avalanche_for_ssd_2cpu_8gb" {
  name         = "avalanche-for-ssd-2cpu-8gb"
  machine_type = "e2-standard-4"
  tags         = ["load-test-traffic"]

  boot_disk {
    initialize_params {
      image = "projects/lma-light-load-testing/global/images/avalanche"
    }
  }

  metadata_startup_script = file(var.avalanche_startup_script)

  network_interface {
    network = google_compute_network.net_lma_light_load_test_net.name

    access_config {
    }
  }
}

resource "google_compute_instance" "vm_locust_for_ssd_2cpu_8gb" {
  name         = "locust-for-ssd-2cpu-8gb"
  machine_type = "e2-standard-2"
  tags         = ["load-test-traffic"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2104-hirsute-v20211119"
    }
  }

  provisioner "file" {
    source      = "prom-query-locustfile.py"
    destination = "/home/ubuntu/prom-query-locustfile.py"

    connection {
      type = "ssh"
      user = "ubuntu"
      #host = self.network_interface[0].access_config[0].nat_ip
      host        = google_compute_instance.vm_locust_for_ssd_2cpu_8gb.network_interface.0.access_config.0.nat_ip
      private_key = file("~/secrets/lma-light-load-testing-ssh")
      #agent = "false"
    }
  }

  #  provisioner "remote-exec" {
  #    inline = [
  #      "chmod +x ~/installations.sh",
  #      "cd ~",
  #      "./installations.sh"
  #    ]
  #    connection {
  #        type = "ssh"
  #        user = "ubuntu"
  #        private_key = "${file("~/.ssh/google_compute_engine")}"
  #    }
  #}

  # TODO use var for gcp internal hostnames
  metadata_startup_script = templatefile(var.locust_startup_script, { PROM_URL = "http://${google_compute_instance.vm_lma_appliance.name}.${var.zone}.c.${var.project}.internal/prom" })

  network_interface {
    network = google_compute_network.net_lma_light_load_test_net.name

    access_config {
    }
  }
}


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
  # avalanhe_url: e.g. vm_avalanche.c.lma-light-load-testing.internal
  avalanche_target = "${google_compute_instance.vm_avalanche.name}.${var.zone}.c.${var.project}.internal"
  prom_url = "http://${google_compute_instance.vm_lma_appliance.name}.${var.zone}.c.${var.project}.internal/prom"

  ssh_keys = <<EOF
    ubuntu:${file(var.ssh_key_public_path)}
  EOF

  file_provisioner_ssh_key = file(var.ssh_key_private_path)

  lma_appliance_resource_name = "${var.disk_type}-${var.ncpus}cpu-${var.gbmem}gb"
}

resource "google_compute_project_metadata" "gcp_metadata" {
  metadata = {
    ssh-keys = local.ssh_keys
  }
}

data "cloudinit_config" "lma" {
  # https://registry.terraform.io/providers/hashicorp/cloudinit/latest/docs/data-sources/cloudinit_config
  # https://github.com/hashicorp/terraform-provider-template/blob/79c2094838bfb2b6bba91dc5b02f5071dd497083/website/docs/d/cloudinit_config.html.markdown
  gzip = false
  base64_encode = false

  part {
    content_type = "text/cloud-config"
    content = file("lma_cloud_init.conf")
    filename = "lma_cloud_init.conf"
  }
}

resource "google_compute_instance" "vm_lma_appliance" {
  name         = local.lma_appliance_resource_name
  machine_type = "custom-${var.ncpus}-${var.gbmem * 1024}"
  tags         = ["load-test-traffic"]

  boot_disk {
    initialize_params {
      image = "projects/lma-light-load-testing/global/images/juju-hirsute-dns-ingress"
      type  = var.disk_type
      size  = "50"
    }
  }

  provisioner "file" {
    content      = templatefile("overlay-load-test.tpl.yaml", { AVALANCHE_URL = local.avalanche_target, PORTS = var.avalanche_ports })
    destination = var.overlay_load_test
    
    connection {
      type = "ssh"
      user = "ubuntu"
      #host = self.network_interface[0].access_config[0].nat_ip
      host        = google_compute_instance.vm_lma_appliance.network_interface.0.access_config.0.nat_ip
      private_key = local.file_provisioner_ssh_key
      #agent = "false"
    }
  }

  metadata_startup_script = templatefile(var.lma_startup_script, { PROJECT = var.project, ZONE = var.zone, INSTANCE = local.lma_appliance_resource_name, OVERLAY_LOAD_TEST = var.overlay_load_test })

  metadata = {
    user-data = "${data.cloudinit_config.lma.rendered}"
  }

  network_interface {
    network = google_compute_network.net_lma_light_load_test_net.name

    access_config {
    }
  }
}

data "cloudinit_config" "avalanche" {
  gzip = false
  base64_encode = false

  part {
    content_type = "text/cloud-config"
    content = file("avalanche.conf")
    filename = "avalanche.conf"
  }
}

resource "google_compute_instance" "vm_avalanche" {
  name         = "avalanche"
  machine_type = "e2-standard-4"
  tags         = ["load-test-traffic"]

  boot_disk {
    initialize_params {
      image = "projects/lma-light-load-testing/global/images/avalanche"
    }
  }

  metadata = {
    user-data = "${data.cloudinit_config.avalanche.rendered}"
  }

  network_interface {
    network = google_compute_network.net_lma_light_load_test_net.name

    access_config {
    }
  }
}

data "cloudinit_config" "locust" {
  gzip = false
  base64_encode = false

  part {
    content_type = "text/cloud-config"
    content = templatefile("locust.tpl.conf", { PROM_URL = local.prom_url })
    filename = "locust.conf"
  }
}

resource "google_compute_instance" "vm_locust" {
  name         = "locust"
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
      host        = google_compute_instance.vm_locust.network_interface.0.access_config.0.nat_ip
      private_key = local.file_provisioner_ssh_key
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

  metadata = {
    user-data = "${data.cloudinit_config.locust.rendered}"
  }

  network_interface {
    network = google_compute_network.net_lma_light_load_test_net.name

    access_config {
    }
  }
}


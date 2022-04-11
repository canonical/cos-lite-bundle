data "cloudinit_config" "avalanche" {
  gzip          = false
  base64_encode = false

  part {
    content_type = "text/cloud-config"
    content = templatefile("prom-scrape-avalanche.tpl.conf", {
      METRIC_COUNT   = var.avalanche_metric_count,
      VALUE_INTERVAL = var.avalanche_value_interval,
      NUM_TARGETS    = var.num_avalanche_targets
    })
    filename = "avalanche.conf"
  }
}

resource "google_compute_instance" "vm_prom_scrape" {
  name         = "avalanche"
  machine_type = "custom-2-8192"
  tags         = ["load-test-traffic", "vm-prom-scrape"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-minimal-2204-lts"
    }
  }

  metadata = {
    user-data = data.cloudinit_config.avalanche.rendered
  }

  network_interface {
    network = google_compute_network.net_cos_lite_load_test_net.name

    access_config {
    }
  }
}


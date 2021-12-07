data "cloudinit_config" "avalanche" {
  gzip          = false
  base64_encode = false

  part {
    content_type = "text/cloud-config"
    content      = templatefile("prom-scrape-avalanche.tpl.conf", { METRIC_COUNT = var.avalanche_metric_count, VALUE_INTERVAL = var.avalanche_value_interval })
    filename     = "avalanche.conf"
  }
}

resource "google_compute_instance" "vm_avalanche" {
  name         = "avalanche"
  machine_type = "custom-4-16384"
  tags         = ["load-test-traffic"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2104-hirsute-v20211119"
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


data "cloudinit_config" "prom_query" {
  gzip          = false
  base64_encode = false

  part {
    content_type = "text/cloud-config"
    content = templatefile("prom-query-locust.tpl.conf", {
      COS_URL     = local.cos_lite_url,
      PROM_URL    = local.prom_url,
      GRAFANA_URL = local.grafana_url,
    })
    filename = "locust.conf"
  }
}

resource "google_compute_instance" "vm_prom_query" {
  name = "prom-query-${count.index}"
  # 4-cpu is not enough for 20 workers (load average: 13.29, 12.20, 9.56, and rising)
  # 8-cpu is not enough for 20 workers (load average: 25.09, 22.40, 22.26)
  # 10-cpu is not enough for 20 workers (load average: 25.87, 24.18, 20.75)
  machine_type = "custom-16-16384"

  # provision several of these VMs because even a "custom-16-16384" is not enough to properly load
  # test with 20 virtual SREs (fetching a dashboard panel of 600 loglines every 5 sec was too much)
  count = var.num_querying_nodes

  tags         = ["load-test-traffic", "vm-prom-query"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2004-focal-v20220204"
      # ubuntu-2110-impish-v20220204
      # ubuntu-2004-focal-v20220204
      # ubuntu-2104-hirsute-v20211119
    }
  }

  provisioner "file" {
    content = templatefile("prom-query-grafana-dashboards.tpl.ts", {
      COS_URL          = local.cos_lite_url,
      GRAFANA_URL      = local.grafana_url,
      REFRESH_INTERVAL = var.prom_scrape_interval,
      NUM_VIRTUAL_SRES = var.num_virtual_sres_per_node,
    })
    destination = "/home/ubuntu/prom-query-grafana-dashboards.ts"

    connection {
      type        = "ssh"
      user        = "ubuntu"
      host        = self.network_interface.0.access_config.0.nat_ip
      private_key = local.file_provisioner_ssh_key
    }
  }

  provisioner "file" {
    content     = file("prom-query-grafana-dashboards.config.js")
    destination = "/home/ubuntu/prom-query-grafana-dashboards.config.js"

    connection {
      type        = "ssh"
      user        = "ubuntu"
      host        = self.network_interface.0.access_config.0.nat_ip
      private_key = local.file_provisioner_ssh_key
    }
  }

  metadata = {
    user-data = data.cloudinit_config.prom_query.rendered
  }

  network_interface {
    network = google_compute_network.net_cos_lite_load_test_net.name

    access_config {
    }
  }
}

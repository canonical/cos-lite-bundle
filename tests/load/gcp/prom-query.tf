data "cloudinit_config" "prom_query" {
  gzip          = false
  base64_encode = false

  part {
    content_type = "text/cloud-config"
    content = templatefile("prom-query-locust.tpl.conf", {
      COS_URL          = local.cos_lite_url,
      PROM_URL         = local.prom_url,
      GRAFANA_URL      = local.grafana_url,
      USERS            = var.prom_query_locust_users,
      NUM_VIRTUAL_SRES = var.num_virtual_sres,
    })
    filename = "locust.conf"
  }
}

resource "google_compute_instance" "vm_prom_query" {
  name         = "locust"
  machine_type = "custom-4-8192"
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
    content = templatefile("prom-query-locustfile.tpl.py", {
      USERS            = var.prom_query_locust_users,
      REFRESH_INTERVAL = var.prom_scrape_interval,
    })
    destination = "/home/ubuntu/prom-query-locustfile.py"

    connection {
      type        = "ssh"
      user        = "ubuntu"
      host        = google_compute_instance.vm_prom_query.network_interface.0.access_config.0.nat_ip
      private_key = local.file_provisioner_ssh_key
    }
  }

  provisioner "file" {
    content = templatefile("prom-query-grafana-dashboards.tpl.ts", {
      COS_URL          = local.cos_lite_url,
      GRAFANA_URL      = local.grafana_url,
      REFRESH_INTERVAL = var.prom_scrape_interval,
    })
    destination = "/home/ubuntu/prom-query-grafana-dashboards.ts"

    connection {
      type        = "ssh"
      user        = "ubuntu"
      host        = google_compute_instance.vm_prom_query.network_interface.0.access_config.0.nat_ip
      private_key = local.file_provisioner_ssh_key
    }
  }

  provisioner "file" {
    content     = file("prom-query-grafana-dashboards.config.js")
    destination = "/home/ubuntu/prom-query-grafana-dashboards.config.js"

    connection {
      type        = "ssh"
      user        = "ubuntu"
      host        = google_compute_instance.vm_prom_query.network_interface.0.access_config.0.nat_ip
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

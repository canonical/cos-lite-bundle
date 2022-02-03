data "cloudinit_config" "loki_log" {
  gzip          = false
  base64_encode = false

  part {
    content_type = "text/cloud-config"
    content      = templatefile("loki-log-locust.tpl.conf", { LOKI_URL = local.loki_url, USERS = var.loki_log_locust_users })
    filename     = "locust.conf"
  }
}


resource "google_compute_instance" "vm_loki_log" {

  # provision this vm only if it is needed for the load test
  count = var.loki_log_lines_per_sec > 0 ? 1 : 0

  name         = "loki-log"
  machine_type = "e2-standard-2"
  tags         = ["load-test-traffic", "vm-loki-log"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2104-hirsute-v20211119"
    }
  }

  provisioner "file" {
    content     = templatefile("loki-log-locustfile.tpl.py", { USERS = var.loki_log_locust_users })
    destination = "/home/ubuntu/loki-log-locustfile.py"

    connection {
      type        = "ssh"
      user        = "ubuntu"
      host        = google_compute_instance.vm_loki_log[count.index].network_interface.0.access_config.0.nat_ip
      private_key = local.file_provisioner_ssh_key
    }
  }

  metadata = {
    user-data = "${data.cloudinit_config.loki_log.rendered}"
  }

  network_interface {
    network = google_compute_network.net_cos_lite_load_test_net.name

    access_config {
    }
  }
}


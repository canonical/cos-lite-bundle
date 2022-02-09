locals {
  # avalanhe_url: e.g. vm_prom_scrape.c.cos-lite-load-testing.internal
  avalanche_target = "${google_compute_instance.vm_prom_scrape.name}.${var.zone}.c.${var.project}.internal"
  prom_url         = "http://${google_compute_instance.vm_cos_lite_appliance.name}.${var.zone}.c.${var.project}.internal/prom"
  loki_url         = "http://${google_compute_instance.vm_cos_lite_appliance.name}.${var.zone}.c.${var.project}.internal/loki"
  grafana_url      = "http://${google_compute_instance.vm_cos_lite_appliance.name}.${var.zone}.c.${var.project}.internal/grafana"

  file_provisioner_ssh_key = file(var.ssh_key_private_path)

  cos_lite_appliance_resource_name = "${var.disk_type}-${var.ncpus}cpu-${var.gbmem}gb"
}

data "cloudinit_config" "cos_lite" {
  # https://registry.terraform.io/providers/hashicorp/cloudinit/latest/docs/data-sources/cloudinit_config
  # https://github.com/hashicorp/terraform-provider-template/blob/79c2094838bfb2b6bba91dc5b02f5071dd497083/website/docs/d/cloudinit_config.html.markdown
  gzip          = false
  base64_encode = false

  part {
    content_type = "text/cloud-config"
    content      = templatefile("cos-lite.tpl.conf", { PROJECT = var.project, ZONE = var.zone, INSTANCE = local.cos_lite_appliance_resource_name, AVALANCHE_URL = local.avalanche_target, NUM_TARGETS = var.num_avalanche_targets, SCRAPE_INTERVAL = var.prom_scrape_interval, GRAFANA_ADMIN_PASSWORD = var.grafana_admin_password })
    filename     = "cos_lite.conf"
  }
}

resource "google_compute_instance" "vm_cos_lite_appliance" {
  name         = local.cos_lite_appliance_resource_name
  machine_type = "custom-${var.ncpus}-${var.gbmem * 1024}"
  tags         = ["load-test-traffic", "vm-cos-lite-appliance"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2104-hirsute-v20211119"
      type  = var.disk_type
      size  = "50"
    }
  }

  metadata = {
    user-data = "${data.cloudinit_config.cos_lite.rendered}"
  }

  network_interface {
    network = google_compute_network.net_cos_lite_load_test_net.name

    access_config {
    }
  }
}


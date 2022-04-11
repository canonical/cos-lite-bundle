locals {
  cos_lite_appliance_resource_name = "${var.disk_type}-${var.ncpus}cpu-${var.gbmem}gb"

  cos_appliance_hostname = "${local.cos_lite_appliance_resource_name}.${var.zone}.c.${var.project}.internal"
  cos_lite_url           = "http://${local.cos_appliance_hostname}"
  prom_url               = "http://${local.cos_appliance_hostname}/${var.juju_model_name}-prometheus-0"
  loki_url               = "http://${local.cos_appliance_hostname}/${var.juju_model_name}-loki-0"
  grafana_url            = "http://${local.cos_appliance_hostname}/${var.juju_model_name}-grafana"

  # avalanche_url: e.g. vm_prom_scrape.c.cos-lite-load-testing.internal
  avalanche_target = "${google_compute_instance.vm_prom_scrape.name}.${var.zone}.c.${var.project}.internal"
}

data "cloudinit_config" "cos_lite" {
  # https://registry.terraform.io/providers/hashicorp/cloudinit/latest/docs/data-sources/cloudinit_config
  # https://github.com/hashicorp/terraform-provider-template/blob/79c2094838bfb2b6bba91dc5b02f5071dd497083/website/docs/d/cloudinit_config.html.markdown
  gzip          = false
  base64_encode = false

  part {
    content_type = "text/cloud-config"
    content = templatefile("cos-lite.tpl.conf", {
      PROJECT                = var.project,
      ZONE                   = var.zone,
      INSTANCE               = local.cos_lite_appliance_resource_name,
      AVALANCHE_URL          = local.avalanche_target,
      NUM_TARGETS            = var.num_avalanche_targets,
      SCRAPE_INTERVAL        = var.prom_scrape_interval,
      COS_APPLIANCE_HOSTNAME = local.cos_appliance_hostname,
      PROM_EXTERNAL_URL      = local.prom_url,
      GRAFANA_EXTERNAL_URL   = local.grafana_url,
      JUJU_MODEL_NAME        = var.juju_model_name,
    })
    filename = "cos_lite.conf"
  }
}

resource "google_compute_instance" "vm_cos_lite_appliance" {
  name         = local.cos_lite_appliance_resource_name
  machine_type = "custom-${var.ncpus}-${var.gbmem * 1024}"
  tags         = ["load-test-traffic", "vm-cos-lite-appliance"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-minimal-2204-lts"
      type  = var.disk_type
      size  = "100"
    }
  }

  metadata = {
    user-data = data.cloudinit_config.cos_lite.rendered
  }

  network_interface {
    network = google_compute_network.net_cos_lite_load_test_net.name

    access_config {
    }
  }
}


locals {
  prom_scrape_hostname = "${google_compute_instance.vm_prom_scrape.name}.${var.zone}.c.${var.project}.internal"

  loki_target                 = "${local.cos_appliance_hostname}:80"
  prom_target                 = "${local.cos_appliance_hostname}:80"
  grafana_target              = "${local.cos_appliance_hostname}:80"
  cos_exporter_target         = "${local.cos_appliance_hostname}:29100"
  cos_pod_top_exporter_target = "${local.cos_appliance_hostname}:29101"
  prom_scrape_exporter_target = "${local.prom_scrape_hostname}:29100"
  loki_log_exporter_targets   = [for i in range(length(google_compute_instance.vm_loki_log)) : "'${google_compute_instance.vm_loki_log[i].name}.${var.zone}.c.${var.project}.internal:29100'"]
  prom_query_exporter_targets = [for i in range(length(google_compute_instance.vm_prom_query)) : "'${google_compute_instance.vm_prom_query[i].name}.${var.zone}.c.${var.project}.internal:29100'"]


  loki_metrics_path    = "/${var.juju_model_name}-loki-0/metrics"
  prom_metrics_path    = "/${var.juju_model_name}-prometheus-0/metrics"
  grafana_metrics_path = "/${var.juju_model_name}-grafana/metrics"
}

data "cloudinit_config" "monitoring" {
  gzip          = false
  base64_encode = false

  part {
    content_type = "text/cloud-config"
    filename     = "monitoring.conf"

    content = yamlencode(
      {
        "write_files" : [
          {
            "path" : "/var/agent.yaml",
            "content" : templatefile("monitoring/agent.tpl.yaml", {
              REMOTE_WRITE_URL             = var.grafana_cloud_remote_write_url,
              REMOTE_WRITE_USERNAME        = var.grafana_cloud_username,
              REMOTE_WRITE_PASSWORD        = var.grafana_cloud_password
              TARGET_COS_APPLIANCE_GRAFANA = local.grafana_target
              TARGET_COS_APPLIANCE_LOKI    = local.loki_target
              TARGET_COS_APPLIANCE_PROM    = local.prom_target
              TARGET_COS_EXPORTER          = local.cos_exporter_target
              TARGET_COS_POD_TOP_EXPORTER  = local.cos_pod_top_exporter_target
              TARGET_LOKI_LOG_EXPORTER     = join(", ", local.loki_log_exporter_targets)
              TARGET_PROM_QUERY_EXPORTER   = join(", ", local.prom_query_exporter_targets)
              TARGET_PROM_SCRAPE_EXPORTER  = local.prom_scrape_exporter_target

              METRICS_PATH_GRAFANA = local.grafana_metrics_path
              METRICS_PATH_LOKI    = local.loki_metrics_path
              METRICS_PATH_PROM    = local.prom_metrics_path
            }),
          },
          {
            "path" : "/etc/systemd/system/grafana-agent.service",
            "content" : file("monitoring/grafana-agent.service"),
          },
          {
            "path" : "/var/wait-for-prom-ready.sh",
            "permissions" : "0755",
            "content" : templatefile("common/wait-for-prom-ready.tpl.sh", {
              PROM_EXTERNAL_URL = local.prom_url,
            }),
          },
        ],

        "package_update" : "true",
        "package_upgrade": "true",
        "package_reboot_if_required": "true",

        "packages" : [
          "unzip",
          "jq",
          "kitty-terminfo",
          "iputils-ping",
        ],

        "runcmd" : [
          file("monitoring/runcmd.sh"),
        ]
    })
  }
}

resource "google_compute_instance" "vm_monitoring" {
  # provision this vm only if grafana cloud is enabled
  count = var.grafana_cloud_enabled == true ? 1 : 0

  name         = "monitoring"
  machine_type = "custom-2-4096"
  tags         = ["load-test-traffic", "vm-monitoring"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-minimal-2204-lts"
    }
  }

  metadata = {
    user-data = data.cloudinit_config.monitoring.rendered
  }

  network_interface {
    network = google_compute_network.net_cos_lite_load_test_net.name

    access_config {
    }
  }
}


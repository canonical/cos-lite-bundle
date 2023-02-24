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
    filename     = "cos_lite.conf"
    content = yamlencode(
      {
        "write_files" : [
          {
            "path" : "/etc/systemd/system/node-exporter.service",
            "content" : file("common/node-exporter.service"),
          },
          {
            "path" : "/run/wait-for-prom-ready.sh",
            "permissions" : "0755",
            "content" : templatefile("common/wait-for-prom-ready.tpl.sh", {
              PROM_EXTERNAL_URL = local.prom_url,
            }),
          },
          {
            "path" : "/run/wait-for-grafana-ready.sh",
            "permissions" : "0755",
            "content" : templatefile("cos-lite/wait-for-grafana-ready.tpl.sh", {
              GRAFANA_EXTERNAL_URL = local.grafana_url,
            }),
          },
          {
            "path" : "/etc/systemd/system/prometheus-stdout-logger.service",
            "content" : templatefile("cos-lite/prometheus-stdout-logger.tpl.service", {
              JUJU_MODEL_NAME = var.juju_model_name,
            }),
          },
          {
            "path" : "/run/pod_top_exporter.py",
            "permissions" : "0755",
            "content" : templatefile("cos-lite/pod_top_exporter.tpl.py", {
              JUJU_MODEL_NAME = var.juju_model_name,
            }),
          },
          {
            "path" : "/etc/systemd/system/pod-top-exporter.service",
            "content" : file("cos-lite/pod-top-exporter.service"),
          },
          {
            "path" : "/run/overlay-load-test.yaml",
            "content" : templatefile("cos-lite/overlay-load-test.tpl.yaml", {
              COS_APPLIANCE_HOSTNAME = local.cos_appliance_hostname,
              NUM_TARGETS            = var.num_avalanche_targets,
              AVALANCHE_URL          = local.avalanche_target,
              SCRAPE_INTERVAL        = var.prom_scrape_interval,
            }),
          },
          {
            "path" : "/run/cos-lite-rest-server.py",
            "permissions" : "0755",
            "content" : file("cos-lite/cos-lite-rest-server.py"),
          },
          {
            "path" : "/etc/systemd/system/cos-lite-rest-server.service",
            "content" : file("cos-lite/cos-lite-rest-server.service"),
          },
        ],

        "package_update" : "true",

        "packages" : [
          "python3-pip",
          "jq",
          "iftop",
          "net-tools",
          "tcptrack",
          "kitty-terminfo",
          "iputils-ping",
          "sysstat",
          "python3-flask",
        ],

        "snap" : {
          "commands" : [
            "snap install --classic juju --channel=2.9/stable",
            "snap install --classic microk8s --channel=1.24/stable",
            "snap alias microk8s.kubectl kubectl",
            "snap refresh",
          ]
        }

        "runcmd" : [
          templatefile("cos-lite/runcmd.tpl.sh", {
            JUJU_MODEL_NAME        = var.juju_model_name,
            PROM_URL               = local.prom_url,
            GRAFANA_URL            = local.grafana_url,
            COS_APPLIANCE_HOSTNAME = local.cos_appliance_hostname,
            PROJECT                = var.project,
            ZONE                   = var.zone,
            INSTANCE               = local.cos_lite_appliance_resource_name,
          }),
        ]
      }
    )
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


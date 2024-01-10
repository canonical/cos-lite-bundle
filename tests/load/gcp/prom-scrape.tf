data "cloudinit_config" "avalanche" {
  gzip          = false
  base64_encode = false

  part {
    content_type = "text/cloud-config"
    filename     = "avalanche.conf"
    content = yamlencode(
      {
        "write_files" : [
          {
            "path" : "/etc/systemd/system/node-exporter.service",
            "content" : file("common/node-exporter.service"),
          },
          {
            "path" : "/etc/systemd/system/avalanche@.service",
            "content" : templatefile("prom-scrape/avalanche@.tpl.service", {
              METRIC_COUNT   = var.avalanche_metric_count,
              VALUE_INTERVAL = var.avalanche_value_interval,
            }),
          },
          {
            "path" : "/etc/systemd/system/avalanche-targets.target",
            "content" : templatefile("prom-scrape/avalanche-targets.tpl.target", {
              NUM_TARGETS = var.num_avalanche_targets,
            }),
          },
        ],
        "package_update" : "true",
        "package_upgrade": "true",
        "package_reboot_if_required": "true",

        "packages" : [
          "git",
          "golang-go",
          "iftop",
          "net-tools",
          "tcptrack",
          "kitty-terminfo",
          "iputils-ping",
        ],

        "runcmd" : [
          file("prom-scrape/runcmd.sh"),
        ]
      }
    )
  }
}

resource "google_compute_instance" "vm_prom_scrape" {
  name         = "avalanche"
  machine_type = "custom-4-16384"
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


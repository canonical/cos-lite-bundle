data "cloudinit_config" "loki_log" {
  gzip          = false
  base64_encode = false

  part {
    content_type = "text/cloud-config"
    filename     = "locust.conf"
    content = yamlencode(
      {
        "write_files" : [
          {
            "path" : "/etc/systemd/system/node-exporter.service",
            "content" : file("common/node-exporter.service"),
          },
          {
            "path" : "/etc/systemd/system/locust@.service",
            "content" : templatefile("loki-log/locust@.tpl.service", {
              LOKI_URL          = local.loki_url,
              LOGGING_SOURCES   = var.num_logging_sources,
              LOG_LINES_PER_SEC = var.loki_log_lines_per_source_per_sec,
            }),
          },
          {
            "path" : "/etc/systemd/system/locust-loggers.target",
            "content" : templatefile("loki-log/locust-loggers.tpl.target", {
              NUM_USERS = var.loki_log_num_locust_users,
            }),
          },
          {
            "path" : "/home/ubuntu/loki-log-locustfile.py",
            "content" : templatefile("loki-log/loki-log-locustfile.tpl.py", {
              POSTING_PERIOD = var.loki_log_post_period
            }),
          },
        ],

        "package_update" : "true",
        "package_upgrade": "true",
        "package_reboot_if_required": "true",

        "packages" : [
          "python3-pip",
          "iftop",
          "jq",
          "kitty-terminfo",
        ],

        "runcmd" : [
          templatefile("loki-log/runcmd.tpl.sh", {
            LOKI_URL = local.loki_url,
          }),
        ]
      }
    )
  }
}


resource "google_compute_instance" "vm_loki_log" {

  # provision this vm only if it is needed for the load test
  count = var.loki_log_lines_per_source_per_sec > 0 ? 1 : 0

  name = "loki-log"

  machine_type = "custom-6-5632"
  allow_stopping_for_update = true

  tags = ["load-test-traffic", "vm-loki-log"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-minimal-2204-lts"
    }
  }

  metadata = {
    user-data = data.cloudinit_config.loki_log.rendered
  }

  network_interface {
    network = google_compute_network.net_cos_lite_load_test_net.name

    access_config {
    }
  }
}

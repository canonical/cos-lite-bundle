data "cloudinit_config" "prom_query" {
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
            "path" : "/etc/systemd/system/flood-element-grafana.service",
            "content" : file("prom-query/flood-element-grafana.service"),
          },
          {
            "path" : "/home/ubuntu/prom-query-grafana-dashboards.ts",
            "content" : templatefile("prom-query/prom-query-grafana-dashboards.tpl.ts", {
              COS_URL          = local.cos_lite_url,
              GRAFANA_URL      = local.grafana_url,
              REFRESH_INTERVAL = var.prom_scrape_interval,
              NUM_VIRTUAL_SRES = var.num_virtual_sres_per_node,
            }),
          },
          {
            "path" : "/home/ubuntu/prom-query-grafana-dashboards.config.js",
            "content" : file("prom-query/prom-query-grafana-dashboards.config.js"),
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
        ],

        "runcmd" : [
          templatefile("prom-query/runcmd.tpl.sh", {
            COS_URL     = local.cos_lite_url,
            PROM_URL    = local.prom_url,
            GRAFANA_URL = local.grafana_url,
          }),
        ]
      }
    )
  }
}

resource "google_compute_instance" "vm_prom_query" {

  # provision several of these VMs because even a "custom-16-16384" is not enough to properly load
  # test with 20 virtual SREs (fetching a dashboard panel of 600 loglines every 5 sec was too much)
  count = var.num_querying_nodes

  name = "prom-query-${count.index}"
  # 4-cpu is not enough for 20 workers (load average: 13.29, 12.20, 9.56, and rising)
  # 8-cpu is not enough for 20 workers (load average: 25.09, 22.40, 22.26)
  # 10-cpu is not enough for 20 workers (load average: 25.87, 24.18, 20.75)
  machine_type = "custom-16-16384"

  tags = ["load-test-traffic", "vm-prom-query"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-minimal-2204-lts"
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


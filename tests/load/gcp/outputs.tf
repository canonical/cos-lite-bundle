output "ip_nat_vm_cos_lite_appliance" {
  value = google_compute_instance.vm_cos_lite_appliance.network_interface.0.access_config.0.nat_ip
}

output "ip_nat_vm_prom_scrape" {
  value = google_compute_instance.vm_prom_scrape.network_interface.0.access_config.0.nat_ip
}

output "ip_nat_vm_prom_query" {
  value = google_compute_instance.vm_prom_query.*.network_interface.0.access_config.0.nat_ip
}

output "ip_nat_vm_loki_log" {
  value = google_compute_instance.vm_loki_log.*.network_interface.0.access_config.0.nat_ip
}

output "ip_nat_vm_monitoring" {
  value = google_compute_instance.vm_monitoring.*.network_interface.0.access_config.0.nat_ip
}

output "data_points_per_minute" {
  # The number of data points per minute is equal to:
  # avalanche_metric_count * 10 * num_scrape_targets / (prom_scrape_interval / 60)
  # (times 10 because there are 10 "series" per metric)
  value = var.avalanche_metric_count * 10 * var.num_avalanche_targets / (var.prom_scrape_interval / 60)
}

output "logged_lines_per_minute" {
  # The number of log lines per minute is equal to:
  # loki_log_num_locust_users * num_logging_sources * loki_log_lines_per_source_per_sec * 60
  value = var.loki_log_num_locust_users * var.num_logging_sources * var.loki_log_lines_per_source_per_sec * 60
}

output "num_virtual_sres" {
  # Total number of virtual SREs
  value = var.num_querying_nodes * var.num_virtual_sres_per_node
}


# The following are used in healthchecks.sh.

output "prom_internal_url" {
    value = local.prom_url
}

output "loki_internal_url" {
    value = local.loki_url
}

output "avalanche_internal_address" {
    value = local.avalanche_target
}

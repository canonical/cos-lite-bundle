output "ip_vm_cos_lite_appliance" {
  value = google_compute_instance.vm_cos_lite_appliance.network_interface.0.network_ip
}

output "ip_nat_vm_cos_lite_appliance" {
  value = google_compute_instance.vm_cos_lite_appliance.network_interface.0.access_config.0.nat_ip
}

output "ip_vm_prom_scrape" {
  value = google_compute_instance.vm_prom_scrape.network_interface.0.network_ip
}

output "ip_nat_vm_prom_scrape" {
  value = google_compute_instance.vm_prom_scrape.network_interface.0.access_config.0.nat_ip
}


output "ip_vm_prom_query" {
  value = google_compute_instance.vm_prom_query.network_interface.0.network_ip
}

output "ip_nat_vm_prom_query" {
  value = google_compute_instance.vm_prom_query.network_interface.0.access_config.0.nat_ip
}

output "ip_vm_loki_log" {
  value = google_compute_instance.vm_loki_log.*.network_interface.0.network_ip
}

output "ip_nat_vm_loki_log" {
  value = google_compute_instance.vm_loki_log.*.network_interface.0.access_config.0.nat_ip
}

output "data_points_per_minute" {
  # The number of data points per minute is equal to:
  # avalanche_metric_count * 10 * num_scrape_targets / (prom_scrape_interval / 60)
  # (times 10 because there are 10 "series" per metric)
  value = var.avalanche_metric_count * 10 * var.num_avalanche_targets / (var.prom_scrape_interval / 60)
}

output "prom_heavy_query_range_in_sec" {
  # How far back need to query prom for to end up fetching 11k datapoints
  # This simulates full reload of the dashboard as if an SRE just opened their browsers
  # It is also how long the load test needs to run for before that amount of data is collected
  # NOTE: assuming --series-count=10 (each avalanche metric has "series" labels 0..9) so the
  # range of the query can be 10 times shorter.
  # This calculation is using the scrape interval to avoid needing data interpolation on
  # prometheus side with queries such as:
  # "/api/v1/query?query=rate(avalanche_metric_mmmmm_0_0[5m])[3300s:300ms]"
  # See the prom-query-locustfile.tpl.py file.
  value = 11000 / 10 * var.prom_scrape_interval
}


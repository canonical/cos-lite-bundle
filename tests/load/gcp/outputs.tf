output "ip_vm_lma_appliance" {
  value = google_compute_instance.vm_lma_appliance.network_interface.0.network_ip
}

output "ip_nat_vm_lma_appliance" {
  value = google_compute_instance.vm_lma_appliance.network_interface.0.access_config.0.nat_ip
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

output "data_points_per_minute" {
  # The number of data points per minute is equal to:
  # avalanche_metric_count * 10 * num_scrape_targets / (prom_scrape_interval / 60)
  # (times 10 because there are 10 "series" per metric)
  value = var.avalanche_metric_count * 10 * var.num_avalanche_targets / (var.prom_scrape_interval / 60)
}


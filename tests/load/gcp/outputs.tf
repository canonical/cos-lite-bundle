output "ip_vm_lma_appliance" {
  value = google_compute_instance.vm_lma_appliance.network_interface.0.network_ip
}

output "ip_nat_vm_lma_appliance" {
  value = google_compute_instance.vm_lma_appliance.network_interface.0.access_config.0.nat_ip
}


output "ip_vm_avalanche" {
  value = google_compute_instance.vm_avalanche.network_interface.0.network_ip
}

output "ip_nat_vm_avalanche" {
  value = google_compute_instance.vm_avalanche.network_interface.0.access_config.0.nat_ip
}


output "ip_vm_locust" {
  value = google_compute_instance.vm_locust.network_interface.0.network_ip
}

output "ip_nat_vm_locust" {
  value = google_compute_instance.vm_locust.network_interface.0.access_config.0.nat_ip
}

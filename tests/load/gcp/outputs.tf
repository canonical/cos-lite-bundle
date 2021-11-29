output "ip_vm_ssd_2cpu_8gb" {
  value = google_compute_instance.vm_lma_appliance.network_interface.0.network_ip
}

output "ip_nat_vm_ssd_2cpu_8gb" {
  value = google_compute_instance.vm_lma_appliance.network_interface.0.access_config.0.nat_ip
}


output "ip_vm_avalanche_for_ssd_2cpu_8gb" {
  value = google_compute_instance.vm_avalanche_for_ssd_2cpu_8gb.network_interface.0.network_ip
}

output "ip_nat_vm_avalanche_for_ssd_2cpu_8gb" {
  value = google_compute_instance.vm_avalanche_for_ssd_2cpu_8gb.network_interface.0.access_config.0.nat_ip
}


output "ip_vm_locust_for_ssd_2cpu_8gb" {
  value = google_compute_instance.vm_locust_for_ssd_2cpu_8gb.network_interface.0.network_ip
}

output "ip_nat_vm_locust_for_ssd_2cpu_8gb" {
  value = google_compute_instance.vm_locust_for_ssd_2cpu_8gb.network_interface.0.access_config.0.nat_ip
}

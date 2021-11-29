variable "project" {
  type = string
  description = "Name of GCP project"
  default = "lma-light-load-testing"
}

variable "credentials_file" {
  type = string
  description = "Path to the JSON key file for editing GCP resources"
  default = "~/secrets/lma-light-load-testing-e767258f9d07.json"
}

variable "region" {
  type = string
  description = "GCP region"
  default = "us-central1"
}

variable "zone" {
  type = string
  description = "GCP zone"
  default = "us-central1-a"
}

variable "lma_startup_script" {
  type = string
  description = "Path to (template) LMA appliance startup script"
  default = "lma_startup_script.tpl.sh"
}

variable "avalanche_startup_script" {
  type = string
  description = "Path to avalanche startup script"
  default = "avalanche_startup_script.sh"
}

variable "locust_startup_script" {
  type = string
  description = "Path to locust startup script"
  default = "locust_startup_script.tpl.sh"
}

variable "overlay_load_test" {
  type = string
  description = "Path in the load test appliance VM to store the overlay file"
  default = "/home/ubuntu/overlay-load-test.yaml"
}

variable "avalanche_ports" {
  type = list(number)
  description = "List of ports (avalanche targets) for LMA appliance to scrape"
  default = [9001, 9002, 9003]
}

variable "disk_type" {
  type = string
  description = "GCP disk type (ssd/magnetic)"
  default = "pd-ssd"
  # default = "pd-standard"
}

variable "ncpus" {
  type = number
  description = "Number of vCPUs for the LMA appliance VM"
  default = 2

  validation {
    condition = can(regex("[0-9][0-9]*", var.ncpus))
    error_message = "The ncpus variable must be an integer."
  }
}

variable "gbmem" {
  type = number
  description = "Amount of memory (GB) for the LMA appliance VM"
  default = 8

  validation {
    condition = can(regex("[0-9][0-9]*", var.gbmem))
    error_message = "The gbmem variable must be an integer."
  }
}

variable "ssh_key_public_path" {
  type = string
  description = "Path to file with public ssh key"
  default = "~/secrets/lma-light-load-testing-ssh.pub"
  sensitive = true
}

variable "ssh_key_private_path" {
  type = string
  description = "Path to file with private ssh key"
  # ssh-keygen -t rsa -b 4096 -f ~/secrets/lma-light-load-testing-ssh -C "" 
  default = "~/secrets/lma-light-load-testing-ssh"
  sensitive = true
}


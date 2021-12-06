#################
# General       #
#################

variable "project" {
  type        = string
  description = "Name of GCP project"
  default     = "lma-light-load-testing"
}

variable "credentials_file" {
  type        = string
  description = "Path to the JSON key file for editing GCP resources"
  default     = "~/secrets/lma-light-load-testing-e767258f9d07.json"
}

variable "region" {
  type        = string
  description = "GCP region"
  default     = "us-central1"
}

variable "zone" {
  type        = string
  description = "GCP zone"
  default     = "us-central1-a"
}

variable "ssh_key_public_path" {
  type        = string
  description = "Path to file with public ssh key"
  default     = "~/secrets/lma-light-load-testing-ssh.pub"
  sensitive   = true
}

variable "ssh_key_private_path" {
  type        = string
  description = "Path to file with private ssh key"
  # ssh-keygen -t rsa -b 4096 -f ~/secrets/lma-light-load-testing-ssh -C "" 
  default   = "~/secrets/lma-light-load-testing-ssh"
  sensitive = true
}


#################
# Avalanche     #
#################

variable "avalanche_ports" {
  type        = list(number)
  description = "List of ports (avalanche targets) for LMA appliance to scrape"
  # Use 20 scrape targets by default and adjust datapoint/min via the metric_count and value_interval variables (which do not have a defaults)
  default = [9001, 9002, 9003, 9004, 9005, 9006, 9007, 9008, 9009, 9010, 9011, 9012, 9013, 9014, 9015, 9016, 9017, 9018, 9019, 9020]
  # default = [9001, 9002, 9003, 9004, 9005, 9006, 9007, 9008, 9009, 9010]
  # default = [9001, 9002, 9003, 9004, 9005]
  # default = [9001]
}

variable "avalanche_metric_count" {
  type        = number
  description = "Number of metrics to generate on each avalanche target."
  # The number of data points per minute is equal to:
  # len(avalanche_ports) * avalanche_metric_count * 10 / (avalanche_value_interval / 60)
  # (times 10 because there are 10 "series" per metric)"

  validation {
    condition     = can(regex("[0-9][0-9]*", var.avalanche_metric_count))
    error_message = "The avalanche_metric_count variable must be an integer."
  }
}

variable "avalanche_value_interval" {
  type        = number
  description = "Refresh period [sec] of metric values; could be shorter than scrape interval"
  default     = 30

  validation {
    condition     = can(regex("[0-9][0-9]*", var.avalanche_value_interval))
    error_message = "The avalanche_value_interval variable must be an integer."
  }
}


#################
# Locust        #
#################

variable "locust_users" {
  type        = number
  description = "Number of locust users to query prometheus"
  # Assume grafana would have 20 dashboards, so 20 locust users
  default = 20

  validation {
    condition     = can(regex("[0-9][0-9]*", var.locust_users))
    error_message = "The locust_users variable must be an integer."
  }
}

variable "locust_log_lines_per_sec" {
  type        = number
  description = "Number of log lines pers second for locust to post to loki"

  validation {
    condition     = can(regex("[0-9][0-9]*", var.locust_log_lines_per_sec))
    error_message = "The locust_log_lines_per_sec variable must be an integer."
  }
}

#################
# LMA appliance #
#################

variable "disk_type" {
  type        = string
  description = "GCP disk type (ssd/magnetic)"

  validation {
    condition     = var.disk_type == "pd-ssd" || var.disk_type == "pd-standard"
    error_message = "The disk_type variable must be one of: 'pd-ssd', 'pd-standard'."
  }
}

variable "ncpus" {
  type        = number
  description = "Number of vCPUs for the LMA appliance VM"

  validation {
    condition     = can(regex("[0-9][0-9]*", var.ncpus))
    error_message = "The ncpus variable must be an integer."
  }
}

variable "gbmem" {
  type        = number
  description = "Amount of memory (GB) for the LMA appliance VM"

  validation {
    condition     = can(regex("[0-9][0-9]*", var.gbmem))
    error_message = "The gbmem variable must be an integer."
  }
}

variable "prom_scrape_interval" {
  type        = number
  description = "Scrape interval (sec) for prom to scrape its targets"
  default     = 15

  validation {
    condition     = can(regex("[0-9][0-9]*", var.prom_scrape_interval))
    error_message = "The prom_scrape_interval variable must be an integer."
  }
}

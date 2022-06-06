#################
# General       #
#################

variable "project" {
  type        = string
  description = "Name of GCP project"
  # TODO: rename to "cos-lite-load-testing"
  default = "lma-light-load-testing"
}

variable "credentials_file" {
  type        = string
  description = "Path to the JSON key file for editing GCP resources"
  default     = "~/secrets/cos-lite-load-testing-e767258f9d07.json"
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
  default     = "~/secrets/cos-lite-load-testing-ssh.pub"
  sensitive   = true
}

variable "ssh_key_private_path" {
  type        = string
  description = "Path to file with private ssh key"
  # ssh-keygen -t rsa -b 4096 -f ~/secrets/cos-lite-load-testing-ssh -C ""
  default   = "~/secrets/cos-lite-load-testing-ssh"
  sensitive = true
}


#################
# Avalanche     #
#################

variable "num_avalanche_targets" {
  type        = number
  description = "Number of avalanche scrape targets to launch and for COS appliance to scrape. The same value is used for num of loggers to Loki."
}

variable "avalanche_metric_count" {
  type        = number
  description = "Number of metrics to generate on each avalanche target."

  validation {
    condition     = can(regex("[0-9][0-9]*", var.avalanche_metric_count))
    error_message = "The avalanche_metric_count variable must be an integer."
  }
}

variable "avalanche_value_interval" {
  type        = number
  description = "Refresh period [sec] of metric values; could be shorter than scrape interval"
  default     = 15

  validation {
    condition     = can(regex("[0-9][0-9]*", var.avalanche_value_interval))
    error_message = "The avalanche_value_interval variable must be an integer."
  }
}


#######################
# Locust (prom_query) #
#######################

variable "num_querying_nodes" {
  type        = number
  description = "Number of querying nodes fetching data from grafana."
  default     = 2

  validation {
    condition     = can(regex("[0-9][0-9]*", var.num_querying_nodes))
    error_message = "The num_querying_nodes variable must be an integer."
  }
}

variable "num_virtual_sres_per_node" {
  type        = number
  description = "Number of virtual SREs per node that reopen a dashboard - as many flood element instances will be started."
  default     = 10

  validation {
    condition     = can(regex("[0-9][0-9]*", var.num_virtual_sres_per_node))
    error_message = "The num_virtual_sres_per_node variable must be an integer."
  }
}

#######################
# Locust (loki_log)   #
#######################

variable "num_logging_sources" {
  type        = number
  description = "Number of logging sources posting logs to Loki."

  validation {
    condition     = can(regex("[0-9][0-9]*", var.num_logging_sources))
    error_message = "The num_logging_sources variable must be an integer."
  }
}

variable "loki_log_lines_per_sec" {
  type        = number
  description = "Number of log lines pers second per (virtual) logging source to post to loki"

  validation {
    condition     = can(regex("[0-9][0-9]*", var.loki_log_lines_per_sec))
    error_message = "The loki_log_lines_per_sec variable must be an integer."
  }
}

variable "loki_log_post_period" {
  type        = number
  description = "Loki log posting interval (sec) between consecutive posts to /loki/api/v1/push"
  default     = 15

  validation {
    condition     = can(regex("[0-9][0-9]*", var.loki_log_post_period))
    error_message = "The loki_log_post_period variable must be an integer."
  }
}

#################
# COS appliance #
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
  description = "Number of vCPUs for the COS appliance VM"

  validation {
    condition     = can(regex("[0-9][0-9]*", var.ncpus))
    error_message = "The ncpus variable must be an integer."
  }
}

variable "gbmem" {
  type        = number
  description = "Amount of memory (GB) for the COS appliance VM"

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

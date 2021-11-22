variable "project" {
  default = "lma-light-load-testing"
}

variable "credentials_file" {
  default = "~/secrets/lma-light-load-testing-e767258f9d07.json"
}

variable "region" {
  default = "us-central1"
}

variable "zone" {
  default = "us-central1-a"
}

variable "lma_startup_script" {
  default = "lma_startup_script.sh"
}

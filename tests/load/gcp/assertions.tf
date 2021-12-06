module "errorcheck_invalid" {
  source = "rhythmictech/errorcheck/terraform"
  version = "~> 1.0.0"

  assert = var.avalanche_metric_count >= var.locust_users
  error_message = "Number of metrics must not be lower than locust users."
}

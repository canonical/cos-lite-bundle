module "errorcheck_invalid" {
  source         = "rhythmictech/errorcheck/terraform"
  version        = "~> 1.3"
  python_program = "python3"
  assert         = var.avalanche_metric_count >= 10
  error_message  = "Number of metrics must not be lower than 10: the grafana dashboard assumes 10."
}

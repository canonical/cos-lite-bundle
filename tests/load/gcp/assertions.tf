module "errorcheck_invalid" {
  source  = "rhythmictech/errorcheck/terraform"
  version = "~> 1.0.0"

  assert        = var.avalanche_metric_count >= var.num_virtual_sres
  error_message = "Number of metrics must not be lower than users."
}

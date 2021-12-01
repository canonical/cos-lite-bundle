# The number of data points per minute is equal to:
# avalanche_metric_count * 10 * 20 / (prom_scrape_interval / 60)
# (times 10 because there are 10 "series" per metric)
# (times 20 because there are 20 scrape targets)
avalanche_metric_count = 100
avalanche_value_interval = 30
prom_scrape_interval = 60

locust_log_lines_per_sec = 100

disk_type = "pd-ssd"
ncpus = 2
gbmem = 4


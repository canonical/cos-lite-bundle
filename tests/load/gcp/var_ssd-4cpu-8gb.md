## Results
- (previously, with locust querying prom directly) 96,000 datapoints per minute
  / 0 log lines per second (12 targets, 200 metrics per target)
- (with flood element) TBD

## Record (using flood element)
| Identifier                    | 2022-04-22 | 2022-00-00 | 2022-00-00 | 2022-00-00 | 2022-00-00 | 2022-00-00 | 2022-00-00 |
|-------------------------------|:----------:|:----------:|:----------:|:----------:|:----------:|:----------:|:----------:|
| Metrics per target            |    200     |    200     |    200     |    200     |    200     |    200     |    200     |
| Avalanche value interval      |     15     |     15     |     15     |     15     |     15     |     15     |     15     |
| Prom scrape interval          |     15     |     15     |     15     |     15     |     15     |     15     |     15     |
| Num virtual SREs              |     20     |     20     |     20     |     20     |     20     |     20     |     20     |
| Dashboard reload period [min] |     5      |     5      |     5      |     5      |     5      |     5      |     5      |
| Scrape/logging targets        |     12     |            |            |            |            |            |            |
| Loki log lines [1/sec]        |     2      |            |            |            |            |            |            |
| Datapoints/min                |   96000    |            |            |            |            |            |            |
| % CPU (p50, p95, p99)         | 20, 24, 24 |            |            |            |            |            |            |
| % mem (p50, p95, p99)         |     29     |            |            |            |            |            |            |
| HTTP request times (p99) [ms] |    24.5    |            |            |            |            |            |            |
| Failed HTTP requests [%]      |    0.09    |            |            |            |            |            |            |
| Storage [GiB/day]             |    1.1     |            |            |            |            |            |            |
| Network tx (avg, max) [MiB/s] |  0.8, 8.5  |            |            |            |            |            |            |
| Network rx [MiB/s]            |    0.07    |            |            |            |            |            |            |
| Disk write [MiB/s] (avg, max) |  0.8, 3.0  |            |            |            |            |            |            |
| Disk write IOPS (avg, max)    |  65, 259   |            |            |            |            |            |            |
| Disk read [MiB/s]             |    0.09    |            |            |            |            |            |            |
| Disk read IOPS                |    4.5     |            |            |            |            |            |            |

### Calculation method
Using node exporter:
- Grafana query success rate [%]: TODO needed? already have % failed
- % cpu: `sum by (instance) (1 - irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100 / (sum by (instance) (count without(cpu, mode) (node_cpu_seconds_total{mode="idle"})))`
  - p99: `quantile_over_time(0.99, (sum by (instance) (1 - irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100 / (sum by (instance) (count without(cpu, mode) (node_cpu_seconds_total{mode="idle"}))))[1h:])`
- % mem: `(node_memory_MemTotal_bytes - node_memory_MemFree_bytes - node_memory_Cached_bytes - node_memory_Slab_bytes - node_memory_Buffers_bytes) / node_memory_MemTotal_bytes * 100`
  - p99: `quantile_over_time(0.99, ((node_memory_MemTotal_bytes - node_memory_MemFree_bytes - node_memory_Cached_bytes - node_memory_Slab_bytes - node_memory_Buffers_bytes)/ node_memory_MemTotal_bytes * 100)[1h:])`
- HTTP request times (p99) [ms]: `histogram_quantile(0.99, sum by (job, le) (rate(grafana_http_request_duration_seconds_bucket[10m]))) * 1000`
- % failed HTTP requests: `((sum (grafana_page_response_status_total{code=~"5.*"})) / (sum (grafana_page_response_status_total))) * 100`
- Storage [GiB/day]: `clamp_max(deriv(node_filesystem_free_bytes{mountpoint=~".*/prometheus/.*"}[30m]), 0)/1e9*24*60*60`
- Network tx [MiB/s]: `rate(node_network_transmit_bytes_total{device!="lo"}[30s]) / 1e6`
- Network rx [MiB/s]: `rate(node_network_receive_bytes_total{device!="lo"}[30s]) / 1e6`
- Disk write [MiB/s]: `rate(node_disk_written_bytes_total[30s]) / 1e6`
- Disk write [IOPS]: `irate(node_disk_writes_completed_total[30s])`
- Disk read [MiB/s]: `rate(node_disk_read_bytes_total[30s]) / 1e6`
- Disk read [IOPS]: `irate(node_disk_reads_completed_total[30s])`

```yaml
# > $ cat /var/snap/prometheus/53/prometheus.yml
# my global config
global:
  scrape_interval:     15s # Set the scrape interval to every 15 seconds. Default is every 1 minute.
  evaluation_interval: 15s # Evaluate rules every 15 seconds. The default is every 1 minute.

# Alertmanager configuration
alerting:
  alertmanagers:
  - static_configs:
    - targets:
      # - alertmanager:9093

# Load rules once and periodically evaluate them according to the global 'evaluation_interval'.
rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

# A scrape configuration containing exactly one endpoint to scrape:
# Here it's Prometheus itself.
scrape_configs:
  # The job name is added as a label `job=<job_name>` to any timeseries scraped from this config.
  - job_name: 'cos-lite-load-test'
    static_configs:
    - targets: ['34.72.72.223:9100']
  - job_name: 'grafana-self'
    static_configs:
    - targets: ['34.72.72.223:80']
    metrics_path: '/grafana/metrics'
```
## Previous record (using locust)

| Identifier                  | 2021-12-08 | 2021-12-10 | 2021-12-13 | 2021-12-14 | 2021-12-15 |  2021-12-15  | 2021-12-16 |
|-----------------------------|:----------:|:----------:|:----------:|:----------:|:----------:|:------------:|:----------:|
| Metrics per target          |     100    |     100    |     200    |    1000    |    1000    |      500     |     200    |
| Avalanche targets           |      5     |      5     |      5     |      5     |     20     |      20      |     20     |
| Avalanche value interval    |     30     |     30     |     30     |     30     |     30     |      30      |     30     |
| Prom scrape interval        |     15     |     15     |     15     |     15     |     15     |      15      |     15     |
| Loki log lines [1/sec]      |      0     |      0     |      0     |      0     |      0     |       0      |      0     |
| Datapoints/min              |   20,000   |   20,000   |   40,000   |   200,000  |   800,000  |    400,000   |   160,000  |
| Locust workers              |     20     |     20     |     200    |     200    |     200    |      200     |     200    |
| Big prom query period [min] |      10    |      5     |      5     |      5     |      5     |       5      |      5     |
| Prom query success rate [%] |            |            |     100    |     100    |     65     |      80      |     76     |
| % CPU                       |     20     |     15     |     40     |     38     |   40-100   |    40-100    |   40-100   |
| % mem                       |     90     |     28     |     33     |     37     | 30~100 OOM |  20~100 OOM  | 20~100 OOM |
| Storage [GiB/day]           |            |            |    0.18    |     0.8    |   unclear  |    unclear   |   unclear  |
| Network tx [MiB/s]          |     1.8    |    0.13    |    1.35    |     1.3    |   0.00063  |       4      |     0~5    |
| Network rx [MiB/s]          |    0.02    |    0.005   |    0.31    |    0.05    |    0.003   |     0.09     |    0.06    |
| Disk write [MiB/s] ~ IOPS   |  0.5 ~ 25  |  0.3 ~ 25  |  0.3 ~ 25  |  0.33 ~ 26 |  0 ~ 0.15  |  0 ~ unclear |  0.35 ~ 14 |
| Disk read [MiB/s] ~ IOPS    |   0.5 ~ 4  |  0 ~ 0.01  |  0 ~ 0.02  |  0 ~ 0.01  |  24 ~ 520  | 24 ~ unclear |  24 ~ 500  |

| Identifier                  | 2021-12-16 | 2021-12-17 | 2022-01-04 | 2022-01-04 | 2022-01-05 | 2022-01-06 |  2022-01-07 |
|-----------------------------|:----------:|:----------:|:----------:|:----------:|:----------:|:----------:|:-----------:|
| Metrics per target          |     200    |     200    |     200    |     200    |     200    |     200    |     200     |
| Avalanche targets           |     10     |     10     |     15     |     13     |     13     |     10     |      12     |
| Avalanche value interval    |     30     |     30     |     30     |     30     |     15     |     15     |      15     |
| Prom scrape interval        |     15     |     15     |     15     |     15     |     15     |     15     |      15     |
| Loki log lines [1/sec]      |      0     |      0     |      0     |      0     |      0     |      0     |      0      |
| Datapoints/min              |   80,000   |   80,000   |   120,000  |   104,000  |   104,000  |   80,000   |    96,000   |
| Locust workers              |     200    |     200    |     200    |     200    |     200    |     200    |     200     |
| Big prom query period [min] |      5     |      5     |      5     |      5     |      5     |      5     |      5      |
| Prom query success rate [%] |     100    |     100    |            |     100    |     95     |     100    |     100     |
| % CPU                       |     73     |     60     |            |    70-80   |   40-100   |    60-70   |    50-95    |
| % mem                       |     64     |     40     |     OOM    |    40-70   |   40-OOM   |    30-50   |    40-60*   |
| Storage [GiB/day]           |    0.345   |     0.4    |            |     0.5    |   unclear  |    0.54    |    0.572    |
| Network tx [MiB/s]          |     2.5    |     2.5    |            |     3.4    |     4.0    |     3.0    |     3-4     |
| Network rx [MiB/s]          |    0.04    |    0.04    |            |    0.05    |    0.06    |    0.05    |     0.06    |
| Disk write [MiB/s] ~ IOPS   |  0.33 ~ 25 |  0.32 ~ 27 |            |  0.34 ~ 25 |            |  0.3 ~ 26  |   0.6 ~ 50  |
| Disk read [MiB/s] ~ IOPS    |  0 ~ 0.05  |  0 ~ 0.01  |            | 0 ~ 0.05-3 |            |  0 ~ 0.04  | 0.005 ~ 0.2 |

### 2021-12-08
Occasionally (2-2.5hrs) the VM would hang and prom get oomkilled.
With the latest prom/prometheus image, encountered a 2-hour hang.

Peak disk read speed: 12MiB/s ~ 255 IOPS

Finding:
Download size is 200M, not 100M as thought previously. Maybe related to scrape interval being
reduced from 60s to 15s but locust query remained the same. Can't see why scrape interval would
change size of interpolated data.


### 2021-12-10
Now the size of the "big query" is only 11k points (reduction by a factor of 20 from before)
This was running for 3 days without issues

### 2021-12-13
Now using 200 locust workers

### 2021-12-14
Attempting 1000 metrics per target

### 2021-12-15
Attempted 20 workers. Kept OOMing repeatedly.
Repeating with 500 metrics per target instead of 1000. OOM.

### 2021-12-16
This runs is with a lower total datapoints/min (160k vs 200k on 2021-12-14),
but with 20 scrape targets instead of 5, and 200 metrics per target instead of 1000.
OOM.
Repeating with 10 workers.

### 2021-12-17
Rerunning previous test, but with a bundle overlay that uses latest prom image.
Memory usage pattern is noticeably different: previously was flat at 60%, now fluctuating under 40%.
Ran stable for 2 days.

### 2022-01-05
Repeat test from yesterday but with avalanche refresh of 15 sec (to match prom interval) instead of 30 sec.
Mem % now fuctuates between 40 and OOM; cpu is near 100%.
This probably means that prom has some optimizations in place when data doesn't change between scrape intervals.
Using 15 sec for avalanche from now on.

### 2022-01-07
Occasional (every ~2-3hrs) short-lived %mem spikes 70-85%.

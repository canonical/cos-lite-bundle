## Results
CPU limited to 4 instances.

## Record
| Identifier                  | 2022-01-17 | 2022-01-18 | 2022-01-19 | 2022-01-20 | 2022-02-04 | 2022-02-06  | 2022-02-07 |
|-----------------------------|:----------:|:----------:|:----------:|:----------:|:----------:|:-----------:|:----------:|
| Metrics per target          |     200    |     200    |     200    |     200    |    200     |     200     |    200     |
| Avalanche targets           |      2     |      4     |      6     |      5     |     8      |     20      |     30     |
| Avalanche value interval    |     15     |     15     |     15     |     15     |     15     |     15      |     15     |
| Prom scrape interval        |     15     |     15     |     15     |     15     |     15     |     15      |     15     |
| Loki log lines [1/sec]      |      0     |      0     |      0     |      0     |     0      |      0      |     0      |
| Datapoints/min              |   16,000   |   32,000   |   48,000   |   40,000   |   64,000   |   160,000   |  240,000   |
| Locust workers              |     200    |     200    |     200    |     200    |    200     |     200     |    200     |
| Big prom query period [min] |      5     |      5     |      5     |      5     |     5      |      5      |     5      |
| Big prom query median [ms]  |     780    |    1900    |    4600    |    3400    |   ~~3~~    |    1300     |            |
| Prom query success rate [%] |     100    |     100    |     85     |    99.7    |    100     |     100     |            |
| % CPU                       |    40-50   |    50-70   |     100    |    60-90   |   ~~25~~   |    50-60    |            |
| % mem                       |     45     |    50-60   |     OOM    |    50-70   |   ~~45~~   |    50-54    |            |
| Storage [GiB/day]           |    0.314   |    0.268   |   unclear  |    0.394   |            |   1.113*    |            |
| Network tx [MiB/s]          |   0.5-0.8  |    1-1.7   |   unclear  |    1-1.8   |    0.01    |    1-1.6    |            |
| Network rx [MiB/s]          |      0     |    0.02    |   unclear  |    0.02    |   0.015    |    0.04     |            |
| Disk write [MiB/s] ~ IOPS   |  0.6 ~ 53  |  0.62 ~ 57 |    0 ~ 0   |  0.5 ~ 43  |    ~ 31    |  0.6 ~ 50   |            |
| Disk read [MiB/s] ~ IOPS    |  0 ~ 0.02  |  0 ~ 0.02  |  24 ~ 340  |  0.05 ~ 6  |   ~ 0.01   | 0.003 ~ 0.2 |            |

## Comments
### 2022-02-04
The heavy locust query was causing prom to do heavy interpolation, and also
didn't take into account that each metric has multiple series (10):

```python
self.client.get("/api/v1/query?query=rate(avalanche_metric_mmmmm_0_0[5m])[3300s:300ms]")
```

The new query avoids interpolating and calculates on its own how long the range
should be to reach 11k datapoints, e.g.:

```python
self.client.get(f"/api/v1/query?query=rate(avalanche_metric_mmmmm_0_0[5m])[16500s:15s]")
```

NOTE: results are invalid because the range in the prom query was formatted as
float (`16500.0`) so prom was very quickly returning an error instead of the
heavy response.

### 2022-02-06
(*) storage data is based on 8hrs of data so might be higher than actual.

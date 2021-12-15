## Record

| Identifier                  | 2021-12-08 | 2021-12-10 | 2021-12-13 | 2021-12-14 | xxxx-xx-xx | xxxx-xx-xx | xxxx-xx-xx |
|-----------------------------|:----------:|:----------:|:----------:|:----------:|:----------:|:----------:|:----------:|
| Metrics per target          |     100    |     100    |     200    |    1000    |            |            |            |
| Avalanche targets           |      5     |      5     |      5     |      5     |            |            |            |
| Prom scrape interval        |     15     |     15     |     15     |     15     |            |            |            |
| Loki log lines [1/sec]      |      0     |      0     |      0     |      0     |            |            |            |
| Datapoints/min              |   20,000   |   20,000   |   40,000   |   200,000  |            |            |            |
| Locust workers              |     20     |     20     |     200    |     200    |            |            |            |
| Big prom query period [min] |      10    |      5     |      5     |      5     |            |            |            |
| Prom query success rate [%] |            |            |     100    |     100    |            |            |            |
| % CPU                       |     20     |     15     |     40     |     38     |            |            |            |
| % mem                       |     90     |     28     |     33     |     37     |            |            |            |
| Storage [GiB/day]           |            |            |    0.18    |     0.8    |            |            |            |
| Network tx [MiB/s]          |     1.8    |    0.13    |    1.35    |     1.3    |            |            |            |
| Network rx [MiB/s]          |    0.02    |    0.005   |    0.31    |    0.05    |            |            |            |
| Disk write [MiB/s] ~ IOPS   |  0.5 ~ 25  |  0.3 ~ 25  |  0.3 ~ 25  |  0.33 ~ 26 |            |            |            |
| Disk read [MiB/s] ~ IOPS    |   0.5 ~ 4  |  0 ~ 0.01  |  0 ~ 0.02  |  0 ~ 0.01  |            |            |            |

## Comments
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


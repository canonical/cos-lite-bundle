## Record

| Identifier                  | 2021-12-08 | 2021-12-10 | 2021-12-13 | 2021-12-14 | 2021-12-15 |  2021-12-15  | 2021-12-16 |
|-----------------------------|:----------:|:----------:|:----------:|:----------:|:----------:|:------------:|:----------:|
| Metrics per target          |     100    |     100    |     200    |    1000    |    1000    |      500     |     200    |
| Avalanche targets           |      5     |      5     |      5     |      5     |     20     |      20      |     20     |
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

| Identifier                  | 2021-12-16 | 2021-12-17 | 2022-01-04 | 2022-01-04 | 2022-01-00 | 2022-01-00 | 2022-01-00 |
|-----------------------------|:----------:|:----------:|:----------:|:----------:|:----------:|:----------:|:----------:|
| Metrics per target          |     200    |     200    |     200    |            |            |            |            |
| Avalanche targets           |     10     |     10     |     15     |     13     |            |            |            |
| Prom scrape interval        |     15     |     15     |     15     |     15     |     15     |     15     |     15     |
| Loki log lines [1/sec]      |      0     |      0     |      0     |      0     |      0     |      0     |      0     |
| Datapoints/min              |   80,000   |   80,000   |   120,000  |   104,000  |            |            |            |
| Locust workers              |     200    |     200    |     200    |     200    |     200    |     200    |     200    |
| Big prom query period [min] |      5     |      5     |      5     |      5     |      5     |      5     |      5     |
| Prom query success rate [%] |     100    |     100    |            |            |            |            |            |
| % CPU                       |     73     |     60     |            |            |            |            |            |
| % mem                       |     64     |     40     |     OOM    |            |            |            |            |
| Storage [GiB/day]           |    0.345   |     0.4    |            |            |            |            |            |
| Network tx [MiB/s]          |     2.5    |     2.5    |            |            |            |            |            |
| Network rx [MiB/s]          |    0.04    |    0.04    |            |            |            |            |            |
| Disk write [MiB/s] ~ IOPS   |  0.33 ~ 25 |  0.32 ~ 27 |            |            |            |            |            |
| Disk read [MiB/s] ~ IOPS    |  0 ~ 0.05  |  0 ~ 0.01  |            |            |            |            |            |

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


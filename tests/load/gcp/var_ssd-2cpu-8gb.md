## Results
* CPU-limited to 6 scrape targets (given underlying assumptions)
* 200 locust workers load prom considerably, to the point that it is CPU-limited to only a few workers
* Querying for uncompacted data is more resource intensive than querying for compacted data


## Record
| Identifier                  | 2022-01-08 | 2022-01-09 | 2022-01-10 | 2022-01-11 |  2022-01-12  | 2022-01-12 | 2022-01-13 |
|-----------------------------|:----------:|:----------:|:----------:|:----------:|:------------:|:----------:|:----------:|
| Metrics per target          |     200    |     300    |     600    |     300    |      200     |     600    |     600    |
| Avalanche targets           |      5     |      5     |      5     |     10     |       7      |      6     |      6     |
| Avalanche value interval    |     15     |     15     |     15     |     15     |      15      |     15     |     15     |
| Prom scrape interval        |     15     |     15     |     15     |     15     |      15      |     15     |     15     |
| Loki log lines [1/sec]      |      0     |      0     |      0     |      0     |       0      |      0     |      0     |
| Datapoints/min              |   40,000   |   60,000   |   120,000  |   120,000  |    56,000    |   144,000  |   144,000  |
| Locust workers              |     200    |     200    |     200    |     200    |      200     |     200    |     20     |
| Big prom query period [min] |      5     |      5     |      5     |      5     |       5      |      5     |      5     |
| Prom query success rate [%] |     100    |     100    |     100    |     65     |     99.6*    |     100    |     100    |
| % CPU                       |    60-95   |    65-95   |    65-95   |     100    |     99.7*    |   75-100   |    27-37   |
| % mem                       |    25-40   |    25-40   |    30-40   |     OOM    |     40-80    |    30-50   |    26-30   |
| Storage [GiB/day]           |    0.318   |    0.51    |    0.812   |   unclear  |     0.682    |    1.016   |            |
| Network tx [MiB/s]          |     1-2    |    1.5-2   |     1.9    |      0     |      2.1     |     2.0    |   0.1-0.3  |
| Network rx [MiB/s]          |    0.02    |    0.03    |    0.04    |    0.003   |     0.03     |    0.04    |    0.02    |
| Disk write [MiB/s] ~ IOPS   |  0.4 ~ 43  |  0.5 ~ 45  |   1 ~ 47   |      0     |   0.5 ~ 40   |  0.5 ~ 45  |  0.5 ~ 46  |
| Disk read [MiB/s] ~ IOPS    |  0 ~ 0.02  |  0 ~ 0.02  |  0 ~ 0.08  |  24 ~ 350  | 0.003 ~ 0.07 |  0 ~ 0.03  |  0 ~ 0.02  |


## Comments
### 2021-01-08
NTA.

### 2021-01-12
Compared to 2022-01-09, this one has less datapoints but 2 more targets.
As a result, memory consumption is higher and storage growth is faster.

*   Prom query success rate is under 100 because of a single period of down time of 1hr early on.
    Since then now additional downtimes.
    
*  This machine, near our working point, is cpu-limited to 6 scrape targets.

### 2022-01-13
Reducing Locust workers from 200 to 20 had a significant reduction in mem and cpu usage.

### 2022-01-14
Repeat the previous test but do the big query for past data (after compaction) to test if the high cpu load
is because of inefficient fetch of uncompacted data.
Indeed, adding an offset of 4h to the locust query 
`/api/v1/query?query=rate(avalanche_metric_mmmmm_0_0[5m] offset 4h)[3300s:300ms]`
reduced memory usage to a stable 24% (vs. 26-30%), cpu to stable 20% (vs 27-37%) and big query response duration from 2400ms to 84ms (not sure why).

We primarily use the default settings for single-node deployment in Splunk, with a few modifications: we removed the event length restriction (`TRUNCATE = 0`) and configured each log line as an individual event (`BREAK_ONLY_BEFORE_DATE = false` and `SHOULD_LINEMERGE = false`).

Data ingestion is handled using `add monitor ${datasets}`. However, we noticed a discrepancy between the raw data size (257.25 GB) and the size ingested by Splunk (254.29 GB), resulting in a data loss of 2.96 GB.

Upon investigation, we found that Splunk overlooked certain files during ingestion:
```
${datasets}/worker1/SecurityAuth-root.audit
${datasets}/worker1/hadoop-root-datanode-8dc59161430b.out
${datasets}/worker1/hadoop-root-datanode-8dc59161430b.out.1
${datasets}/worker1/hadoop-root-datanode-8dc59161430b.out.2
${datasets}/worker1/hadoop-root-datanode-8dc59161430b.out.3
${datasets}/worker1/yarn-root-nodemanager-8dc59161430b.log
${datasets}/worker1/yarn-root-nodemanager-8dc59161430b.log.2018-06-15
${datasets}/worker1/yarn-root-nodemanager-8dc59161430b.log.2018-07-02
${datasets}/worker1/yarn-root-nodemanager-8dc59161430b.log.2018-07-07
${datasets}/worker1/yarn-root-nodemanager-8dc59161430b.log.2018-07-12
${datasets}/worker1/yarn-root-nodemanager-8dc59161430b.log.2018-07-14
${datasets}/worker1/yarn-root-nodemanager-8dc59161430b.log.2018-07-26
${datasets}/worker1/yarn-root-nodemanager-8dc59161430b.out
${datasets}/worker1/yarn-root-nodemanager-8dc59161430b.out.1
${datasets}/worker1/yarn-root-nodemanager-8dc59161430b.out.2
${datasets}/worker1/yarn-root-nodemanager-8dc59161430b.out.3
${datasets}/worker2/SecurityAuth-root.audit
${datasets}/worker2/hadoop-root-datanode-fc8782b06de1.out
${datasets}/worker2/hadoop-root-datanode-fc8782b06de1.out.1
${datasets}/worker2/hadoop-root-datanode-fc8782b06de1.out.2
${datasets}/worker2/hadoop-root-datanode-fc8782b06de1.out.3
${datasets}/worker2/yarn-root-nodemanager-fc8782b06de1.out
${datasets}/worker2/yarn-root-nodemanager-fc8782b06de1.out.1
${datasets}/worker2/yarn-root-nodemanager-fc8782b06de1.out.2
${datasets}/worker2/yarn-root-nodemanager-fc8782b06de1.out.3
${datasets}/worker3/SecurityAuth-root.audit
${datasets}/worker3/hadoop-root-datanode-8ed8bf9ebb0e.out
${datasets}/worker3/hadoop-root-datanode-8ed8bf9ebb0e.out.1
${datasets}/worker3/hadoop-root-datanode-8ed8bf9ebb0e.out.2
${datasets}/worker3/hadoop-root-datanode-8ed8bf9ebb0e.out.3
${datasets}/worker3/yarn-root-nodemanager-8ed8bf9ebb0e.log.2018-07-02
${datasets}/worker3/yarn-root-nodemanager-8ed8bf9ebb0e.log.2018-07-11
${datasets}/worker3/yarn-root-nodemanager-8ed8bf9ebb0e.log.2018-07-12
${datasets}/worker3/yarn-root-nodemanager-8ed8bf9ebb0e.log.2018-07-14
${datasets}/worker3/yarn-root-nodemanager-8ed8bf9ebb0e.out
${datasets}/worker3/yarn-root-nodemanager-8ed8bf9ebb0e.out.1
${datasets}/worker3/yarn-root-nodemanager-8ed8bf9ebb0e.out.2
${datasets}/worker3/yarn-root-nodemanager-8ed8bf9ebb0e.out.3
```
The total size of these files is 1.33 GB. The missing log lines from these non-ingested files contribute to discrepancies in the results of the following queries:

| Query | Actual Result | Expected Result | Difference |
|-------|---------------|-----------------|------------|
| Q3    | 492,017       | 513,893         | 21,876     |
| Q4    | 779,891       | 810,033         | 30,142     |
| Q9    | 1,555,133     | 1,623,002       | 67,869     |
| Q12   | 170,468       | 178,076         | 7,608      |

The remaining 1.63 GB of missing data is still unaccounted for, but they seems to have no impact on the query results (because the non-ingested files cover those).
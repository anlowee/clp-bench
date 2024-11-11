We start the ClickHouse server in daemon mode. To store JSON records, we use a
[single string field][jsonasstring] in ClickHouse, eliminating the need for preprocessing.

For query benchmarking, we operate in [single-thread mode][max_threads] by setting
`max_threads = 1`. Additionally, we configure the
[minimum data volume required for direct I/O access][direct_io] to 1 byte
(`min_bytes_to_use_direct_io = 1`) on the storage disk.

[direct_io]: https://clickhouse.com/docs/en/operations/settings/settings#min_bytes_to_use_direct_io
[jsonasstring]: https://clickhouse.com/docs/en/interfaces/formats#jsonasstring
[max_threads]: https://clickhouse.com/docs/en/operations/settings/settings#max_threads

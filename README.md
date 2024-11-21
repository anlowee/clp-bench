# clp-bench

**clp-bench** is a tool for benchmarking [CLP] and other log management systems. It functions as a 
Python package and includes a [web interface][ui] for displaying benchmark results.

## Requirements

- Docker
- Python v3.10 or higher

# Setup

```shell
python3 -m venv venv
. venv/bin/activate
pip install -e .
```

To view usage instructions, run `clp-bench --help`.

# Results
You can view the current benchmark results [here][CLPBench UI]. The benchmark currently evaluates
ingestion and query performance for the following tools:

| Tool Name                      | Version     |
|--------------------------------|-------------|
| [ClickHouse][ClickHouse]       | 23.3.1.2823 |
| [CLP][CLP]                     | 0.2.0       |
| [clp-s][clp-s]                 | 0.2.0       |
| [Elasticsearch][Elasticsearch] | 8.6.2       |
| `grep`                         | 3.7         |
| [Loki][Loki]                   | 3.0.0       |
| [MongoDB][MongoDB]             | 6.0.19      |
| [Splunk][Splunk]               | 9.3.2       |

Don't see a tool here? Feel free to file a [GitHub issue][new Github Issue] for one or follow this
[guide][adding-results] for how to add one. For a detailed description of the benchmarking 
methodology, see [here][methodology].

[assets]: assets
[ClickHouse]: https://clickhouse.com/
[CLP]: https://github.com/y-scope/clp
[clp-s]: https://docs.yscope.com/clp/main/user-guide/core-clp-s.html
[CLPBench UI]: https://benchmarks.yscope.com/clp/
[dynamically-structured assets template]: assets/dynamically-structured/template
[Elasticsearch]: https://www.elastic.co/downloads/elasticsearch
[Loki]: https://grafana.com/oss/loki/
[MongoDB]: https://www.mongodb.com/
[methodology]: docs/methodology.md
[new Github Issue]: https://github.com/y-scope/clp-bench/issues/new
[adding-results]: docs/adding-results.md
[Splunk]: https://www.splunk.com/
[ui]: ui
[unstructured assets template]: assets/unstructured/template

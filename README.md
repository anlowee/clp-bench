# clp-bench

**clp-bench** is a benchmarking tool designed for [CLP] and other log management systems. It
functions as a Python package and includes a [web interface][ui] for displaying benchmark results.

For a detailed description of the benchmarking methodology, see
[this document](docs/methodology.md).

## Requirements

- Docker
- Python v3.10 or higher

# Setup

```shell
python3 -m venv venv
. venv/bin/activate
pip install -e .
```

To view usage instructions, you can run `clp-bench --help`.

# Contribution (WIP🚧)

We encourage contributions that add benchmark results for various tools to support broader community
development. This section is under construction.

## Adding New Results

To benchmark a new system, duplicate one of the directories in [assets] and update the following
files:

- **`config.yaml`**: Contains essential benchmarking configurations:

  - **`system_metric.enable`**: Toggle to enable system metric monitoring (e.g., memory usage). Set
    to `True` to activate.
  - **`system_metric.memory.ingest_polling_interval`**: Time interval (in seconds) for polling
    memory during data ingestion.
  - **`system_metric.memory.run_query_benchmark_polling_interval`**: Time interval (in seconds) for
    polling memory during query benchmarking.
  - **`container_id`**: Identifier for the benchmark container, generally named as
    `${tool}-clp-bench`.
  - **`assets_path`**: Path to the assets directory in the container. Leave as default unless
    modifying `docker-run.sh` (described below).
  - **`datasets_path`**: Path for datasets in the container; may refer to a file, directory, or file
    pattern. clp-bench does not validate dataset presence.
  - **`hot_run_warm_up_times`**: Number of repetitions for query warm-up in hot run mode before
    measuring latency. This may be automated in the future.
  - **`related_processes`**: List of command substrings (from `ps aux`) to track relevant memory
    usage.
  - **`queries`**: Array of queries for benchmarking; carefully handle escape characters.

- **`docker-build.sh`**: Builds the container as per the `Dockerfile` in the same directory.
  Usually, only the `container_name` variable should be adjusted to match the `container_id` in
  `config.yaml`.

- **`docker-run.sh`**: Runs the container, taking the dataset path as an argument. Typically, only
  the `container_name` variable needs alignment with `container_id` in `config.yaml`.

- **`Dockerfile`**: Used for building the container, ensuring installation of the required tool and
  dependencies.

- **`launch-script.sh`**: Initializes and starts the tool (e.g., if it functions as a server or
  service).

- **`reset-script.sh`**: Prepares a clean environment by removing previous data (e.g., dropping
  tables); runs after `launch-script.sh` in `ingest` mode.

- **`measure-decompressed-size-script.sh`**: Measures the raw dataset size before ingestion.
  Typically unchanged, it takes `datasets_path` from `config.yaml` and uses `du -bc` for size
  calculation in bytes.

- **`ingest-script.sh`**: Handles data ingestion, with clp-bench measuring the total latency of this
  script. Avoid adding extra operations.

- **`measure-compressed-size-script.sh`**: Measures the compressed data size post-ingestion, usually
  via tool-specific methods.

- **`search-script.sh`**: Executes queries specified in `config.yaml`. clp-bench supports two
  benchmarking modes:

  - **Hot run mode**: Runs queries for `hot_run_warm_up_times` to warm up the cache, then measures
    latency.
  - **Cold run mode**: Clears the cache with `clear-cache-script.sh` before measuring latency.

- **`clear-cache-script.sh`**: Clears the tool’s cache, essential for cold runs.

- **`methodology.md`**: Describes specific benchmarking setup details, including tuning and dataset
  preprocessing.

- **`results.json`**: Contains benchmarking results, which are loaded and displayed in the UI:

  - **`target`**: The ID used by the frontend, should be in lowercase. IDs of the same type must be
    unique.
  - **`targetDisplayedName`**: The name to display in the column on the webpage.
  - **`displayedOrder`**: Defines the display order of results; a smaller value places the column
    further to the right.
  - **`isEnable`**: Indicates if the results should be displayed (default is `true`). If set to
    `false`, results won’t appear on the webpage.
  - **`type`**: Specifies data type (1 for Unstructured, 2 for Semi-structured).
  - **`ingestTime`**: Total end-to-end time taken to ingest all dataset data.
  - **`compressedSize`**: The size of compressed data archives.
  - **`avgIngestMem`**: The average memory used during data ingestion.
  - **`metrics`**: An array of query benchmarking results for each metric:
    - **`metric`**: Specifies the type (1 for Hot run, 2 for Cold run).
    - **`avgQueryMem`**: The average memory usage during query benchmarking.
    - **`queryTimes`**: An array of end-to-end query latencies, ordered to match the sequence of
      queries.

[assets]: assets
[CLP]: https://github.com/y-scope/clp
[ui]: ui

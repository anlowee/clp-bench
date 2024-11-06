
# clp-bench

**clp-bench** is a benchmarking tool designed for [CLP] and other log management systems. It functions as a Python package and includes a [web interface][ui] for displaying benchmark results.

For a detailed description of the benchmarking methodology, see [this document](docs/methodology.md).

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

We encourage contributions that add benchmark results for various tools to support broader community development. This section is under construction.

## Adding New Results

To benchmark a new system, duplicate one of the directories in [assets] and update the following files:

- **`config.yaml`**: Contains essential benchmarking configurations:
    - **`system_metric.enable`**: Toggle to enable system metric monitoring (e.g., memory usage). Set to `True` to activate.
    - **`system_metric.memory.ingest_polling_interval`**: Time interval (in seconds) for polling memory during data ingestion.
    - **`system_metric.memory.run_query_benchmark_polling_interval`**: Time interval (in seconds) for polling memory during query benchmarking.
    - **`container_id`**: Identifier for the benchmark container, generally named as `${tool}-clp-bench`.
    - **`assets_path`**: Path to the assets directory in the container. Leave as default unless modifying `docker_run` (described below).
    - **`datasets_path`**: Path for datasets in the container; may refer to a file, directory, or file pattern. clp-bench does not validate dataset presence.
    - **`hot_run_warm_up_times`**: Number of repetitions for query warm-up in hot run mode before measuring latency. This may be automated in the future.
    - **`related_processes`**: List of command substrings (from `ps aux`) to track relevant memory usage.
    - **`queries`**: Array of queries for benchmarking; carefully handle escape characters.

- **`docker_build`**: Builds the container as per the `Dockerfile` in the same directory. Usually, only the `container_name` variable should be adjusted to match the `container_id` in `config.yaml`.

- **`docker_run`**: Runs the container, taking the dataset path as an argument. Typically, only the `container_name` variable needs alignment with `container_id` in `config.yaml`.

- **`Dockerfile`**: Used for building the container, ensuring installation of the required tool and dependencies.

- **`launch_script`**: Initializes and starts the tool (e.g., if it functions as a server or service).

- **`reset_script`**: Prepares a clean environment by removing previous data (e.g., dropping tables); runs after `launch_script` in `ingest` mode.

- **`measure_decompressed_size_script`**: Measures the raw dataset size before ingestion. Typically unchanged, it takes `datasets_path` from `config.yaml` and uses `du -bc` for size calculation in bytes.

- **`ingest_script`**: Handles data ingestion, with clp-bench measuring the total latency of this script. Avoid adding extra operations.

- **`measure_compressed_size_script`**: Measures the compressed data size post-ingestion, usually via tool-specific methods.

- **`search_script`**: Executes queries specified in `config.yaml`. clp-bench supports two benchmarking modes:
    - **Hot run mode**: Runs queries for `hot_run_warm_up_times` to warm up the cache, then measures latency.
    - **Cold run mode**: Clears the cache with `clear_cache_script` before measuring latency.

- **`clear_cache_script`**: Clears the tool’s cache, essential for cold runs.

- **`methodology.md`**: Describes specific benchmarking setup details, including tuning and dataset preprocessing.

[CLP]: https://github.com/y-scope/clp
[ui]: ui
[assets]: assets
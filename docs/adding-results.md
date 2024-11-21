# Contributing

🚧 This section is under construction.

We encourage contributions that add benchmark results for various tools to support broader community
development.

## Adding new results

To benchmark a new system, duplicate either [unstructured assets template] or 
[dynamically-structured assets template] and make necessary changes. Here is an overview of the 
content of the templates.

- **`config.yaml`**: Contains essential benchmarking configurations. For details, please refer 
  to the comments in the `config.yaml` under either [unstructured assets template] or 
  [dynamically-structured assets template]

- **`docker-build.sh`**: Builds the container as per the `Dockerfile` in the same directory.
  Usually, only the `container_name` variable should be adjusted to match the `container_id` in
  `config.yaml`.

- **`docker-run.sh`**: Runs the container, taking the dataset path as an argument. Typically, only
  the `container_name` variable needs alignment with `container_id` in `config.yaml`.

- **`Dockerfile`**: Used for building the container, ensuring installation of the required tool and
  dependencies.

- **`launch.sh`**: Initializes and starts the tool (e.g., if it functions as a server or
  service).

- **`reset.sh`**: Prepares a clean environment by removing previous data (e.g., dropping
  tables); runs after `launch.sh` in `ingest` mode.

- **`measure-decompressed-size.sh`**: Measures the raw dataset size before ingestion.
  Typically unchanged, it takes `datasets_path` from `config.yaml` and uses `du -bc` for size
  calculation in bytes.

- **`ingest.sh`**: Handles data ingestion, with clp-bench measuring the total latency of this
  script. Avoid adding extra operations.

- **`measure-compressed-size.sh`**: Measures the compressed data size post-ingestion, usually
  via tool-specific methods.

- **`search.sh`**: Executes queries specified in `config.yaml`. clp-bench supports two
  benchmarking modes:

  - **Hot-run mode**: Runs queries for `hot_run_warm_up_times` to warm up the cache, then measures
    latency.
  - **Cold-run mode**: Clears the cache with `clear-cache.sh` before measuring latency.

- **`clear-cache.sh`**: Clears the tool's cache, essential for cold runs.

- **`methodology.md`**: Describes specific benchmarking set up details, including tuning and dataset
  preprocessing.

- **`results.json`**: Contains benchmarking results, which are loaded and displayed in the UI:

  - **`target`**: The ID used by the frontend, should be lowercase. IDs of the same type must be
    unique.
  - **`targetDisplayedName`**: The name to display in the column on the webpage.
  - **`displayedOrder`**: Defines the display order of results; a smaller value places the column
    further to the right.
  - **`isEnable`**: Indicates if the results should be displayed (default is `true`). If set to
    `false`, results won't appear on the webpage.
  - **`type`**: Specifies data type (1 for Unstructured, 2 for Dynamically-structured).
  - **`ingestTime`**: Total end-to-end time taken to ingest all dataset data.
  - **`compressedSize`**: The size of compressed archives.
  - **`avgIngestMem`**: The average memory used during ingestion.
  - **`metrics`**: An array of query benchmarking results for each metric:

    - **`metric`**: Specifies the type (1 for Hot run, 2 for Cold run).
    - **`avgQueryMem`**: The average memory usage during query benchmarking.
    - **`queryTimes`**: An array of end-to-end query latencies, ordered to match the sequence of
      queries.
- **binary (optional)**: If the benchmarked tool is run via binary, then you should put a 
  `replace-with-your-tool-binary` file in the assets. 
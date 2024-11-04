import argparse
import logging
import traceback

from .executor import BenchmarkingMode, BenchmarkingSystemMetric, ClpBenchExecutor
from .version import VERSION

# Setup logging
# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Setup console logging
logging_console_handler = logging.StreamHandler()
logging_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
logging_console_handler.setFormatter(logging_formatter)
logger.addHandler(logging_console_handler)


def load_benchmarking_assets(assets_path: str) -> ClpBenchExecutor:
    logger.info(f"Loading benchmarking assets from: {assets_path}")
    return ClpBenchExecutor(assets_path)


def ingest(executor: ClpBenchExecutor):
    logger.info("Ingesting data")
    try:
        executor.start_polling_system_metric(
            BenchmarkingSystemMetric.MEMORY, BenchmarkingMode.INGEST_MODE
        )
        executor.launch(BenchmarkingMode.INGEST_MODE)
        executor.ingest(BenchmarkingMode.INGEST_MODE)
    except Exception as e:
        logger.error(f"Failed to ingest in {BenchmarkingMode.INGEST_MODE.value} mode : {e}")
    finally:
        executor.stop_polling_system_metric(
            BenchmarkingSystemMetric.MEMORY, BenchmarkingMode.INGEST_MODE
        )
        try:
            executor.terminate(BenchmarkingMode.INGEST_MODE)
        except Exception as e:
            logger.error(
                f"Failed to finish benchmark in {BenchmarkingMode.INGEST_MODE.value} mode: {e}"
            )


def run_query_benchmark(
    executor: ClpBenchExecutor, mode: BenchmarkingMode = BenchmarkingMode.HOT_RUN_MODE
):
    logger.info(f"Running benchmarking in {mode.value} mode")
    try:
        executor.start_polling_system_metric(BenchmarkingSystemMetric.MEMORY, mode)
        # Note that no deployment here, it assumes finished ingestion.
        executor.launch(mode)
        executor.run_query_benchmark(mode)
    except Exception as e:
        logger.error(f"Failed to run benchmark in {mode.value} mode: {e}")
    finally:
        executor.stop_polling_system_metric(BenchmarkingSystemMetric.MEMORY, mode)
        try:
            executor.terminate(mode)
        except Exception as e:
            logger.error(f"Failed to finish benchmark in {mode.value} mode: {e}")


def main():
    description = "CLP Bench--An out-of-the-box benchmarking framework."
    # Command line arguments parsing
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-a", "--asset", type=str, required=True, help="The benchmarking asset location"
    )
    parser.add_argument(
        "-m",
        "--mode",
        type=str,
        choices=["hot", "cold", "ingest"],
        required=True,
        help="The benchmarking mode",
    )
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-v", "--version", action="version", version=f"{VERSION}")
    args = parser.parse_args()
    logger.info(f"The benchmarking asset location: {args.asset}")
    logger.info(f"The benchmarking mode: {args.mode}")

    if args.debug:
        logger.info("Enable DEBUG mode")
        logger.setLevel(logging.DEBUG)

    # Load corresponding implementation for executor's SPI
    try:
        executor = load_benchmarking_assets(args.asset)
    except Exception as e:
        traceback.print_exc()
        logger.error(e)
        return

    # Only ingest the data
    if "ingest" == args.mode:
        ingest(executor)

    # Hot run mode with warm cache benchmarking
    if "hot" == args.mode:
        run_query_benchmark(executor, BenchmarkingMode.HOT_RUN_MODE)

    # Cold run mode with cold cache benchmarking
    if "cold" == args.mode:
        run_query_benchmark(executor, BenchmarkingMode.COLD_RUN_MODE)

    executor.visualize()

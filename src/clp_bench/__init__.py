import argparse
import importlib
import logging
import traceback

from .executor import BenchmarkingMode, BenchmarkingSystemMetric, CPTExecutorBase
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


def load_executor_class(target_tool_name: str, config_path: str) -> CPTExecutorBase:
    logger.info("Loading executor implementation for: " + target_tool_name)
    module = importlib.import_module("clp_bench." + target_tool_name.lower() + "_executor")
    cls = getattr(module, "CPTExecutor" + target_tool_name)
    return cls(config_path)


def hot_run_benchmark(executor: CPTExecutorBase):
    logger.info("Running benchmark in hot-run mode")
    try:
        executor.start_polling_system_metric(
            BenchmarkingSystemMetric.MEMORY, BenchmarkingMode.HOT_RUN_MODE
        )
        executor.deploy(BenchmarkingMode.HOT_RUN_MODE)
        executor.launch(BenchmarkingMode.HOT_RUN_MODE)
        executor.ingest(BenchmarkingMode.HOT_RUN_MODE)
        executor.run_query_benchmark(BenchmarkingMode.HOT_RUN_MODE)
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Failed to run benchmark in hot-run mode: {e}")
    finally:
        executor.stop_polling_system_metric(
            BenchmarkingSystemMetric.MEMORY, BenchmarkingMode.HOT_RUN_MODE
        )
        try:
            executor.terminate(BenchmarkingMode.HOT_RUN_MODE)
        except Exception as e:
            logger.error(f"Failed to finish benchmark in hot-run mode: {e}")


def cold_run_benchmark(executor: CPTExecutorBase):
    logger.info("Running benchmarking in cold-run mode")
    try:
        executor.start_polling_system_metric(
            BenchmarkingSystemMetric.MEMORY, BenchmarkingMode.COLD_RUN_MODE
        )
        executor.deploy(BenchmarkingMode.COLD_RUN_MODE)
        executor.launch(BenchmarkingMode.COLD_RUN_MODE)
        executor.ingest(BenchmarkingMode.COLD_RUN_MODE)
        executor.mid_terminate(BenchmarkingMode.COLD_RUN_MODE)
        executor.launch(BenchmarkingMode.COLD_RUN_MODE)
        executor.run_query_benchmark(BenchmarkingMode.COLD_RUN_MODE)
    except Exception as e:
        logger.error(f"Failed to run benchmark in cold-run mode: {e}")
    finally:
        executor.stop_polling_system_metric(
            BenchmarkingSystemMetric.MEMORY, BenchmarkingMode.COLD_RUN_MODE
        )
        try:
            executor.terminate(BenchmarkingMode.COLD_RUN_MODE)
        except Exception as e:
            logger.error(f"Failed to finish benchmark in cold-run mode: {e}")


def ingest(executor: CPTExecutorBase):
    logger.info("Ingesting data")
    try:
        executor.start_polling_system_metric(
            BenchmarkingSystemMetric.MEMORY, BenchmarkingMode.INGEST_MODE
        )
        executor.deploy(BenchmarkingMode.INGEST_MODE)
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
    executor: CPTExecutorBase, mode: BenchmarkingMode = BenchmarkingMode.HOT_RUN_MODE
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
    unstructured_choices = [
        "GrafanaLoki",
        "CLPG",
        "GLT",
        "Grep",
        "ElasticsearchUnstructured",
    ]
    semi_structured_choices = [
        "CLPJson",
        "CLPS",
        "Elasticsearch",
        "MongoDB",
    ]
    # Command line arguments parsing
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-t",
        "--target",
        type=str,
        choices=unstructured_choices + semi_structured_choices,
        required=True,
        help="The target tool you want to benchmark",
    )
    parser.add_argument(
        "-c", "--config", type=str, default="./config.yaml", help="The yaml config file location"
    )
    parser.add_argument(
        "-m",
        "--mode",
        type=str,
        choices=["all", "hot", "cold", "query-only", "hotv2", "coldv2", "ingest"],
        default="all",
        help="The benchmarking mode",
    )
    parser.add_argument("-v", "--version", action="version", version=f"{VERSION}")
    args = parser.parse_args()
    logger.info(f"Target tool is {args.target}")
    logger.info(f"The config file location: {args.config}")
    logger.info(f"The benchmarking mode: {args.mode}")

    # Load corresponding implementation for executor's SPI
    try:
        executor = load_executor_class(args.target, args.config)
    except Exception as e:
        traceback.print_exc()
        logger.error(e)
        return

    # Hot run mode with warm cache benchmarking
    if "all" == args.mode or "hot" == args.mode:
        hot_run_benchmark(executor)

    # Cold run mode with cold cache benchmarking
    if "all" == args.mode or "cold" == args.mode:
        cold_run_benchmark(executor)

    # Query only run mode, assuming just finished a hot run or cold run
    if "query-only" == args.mode:
        run_query_benchmark(executor)

    if "ingest" == args.mode:
        ingest(executor)

    if "hotv2" == args.mode:
        run_query_benchmark(executor, BenchmarkingMode.HOT_RUN_MODE)

    if "coldv2" == args.mode:
        run_query_benchmark(executor, BenchmarkingMode.COLD_RUN_MODE)

    executor.visualize()

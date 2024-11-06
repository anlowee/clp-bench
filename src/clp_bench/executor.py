import logging
import statistics
import subprocess
import threading
import time
from enum import Enum
from typing import Dict, List

import yaml

logger = logging.getLogger(__name__)


class BenchmarkingMode(Enum):
    """
    Enumeration class for different benchmarking modes in CLP Bench.

    This class defines the modes in which the CLP Bench can operate, each representing a distinct
    way to execute and analyze the benchmarking process.

    Attributes:
        HOT_RUN_MODE
            Represents a "hot run" where the system may utilize warmed caches.
        COLD_RUN_MODE
            Represents a "cold run" where caches are typically cleared to simulate a cold start
            scenario.
        INGEST_MODE
            Represents an "ingest" mode, focusing on data ingestion without querying.
    """

    HOT_RUN_MODE = "hot run"
    COLD_RUN_MODE = "cold run"
    INGEST_MODE = "ingest"


class BenchmarkingStage(Enum):
    """
    Enumeration class for different stages in the benchmarking process of CLP
    Bench.

    This class defines the stages in the benchmarking workflow, each representing a specific phase
    of operation in CLP Bench. Note that currently this class has no use, but leave here for
    reserving flexibility.

    Attributes:
        INGEST
            Represents the ingestion stage, where data is ingested into the system for
            benchmarking.
        RUN_QUERY_BENCHMARK
            Represents the query benchmarking stage, where performance is measured based on query
            execution.
    """

    INGEST = "ingest"
    RUN_QUERY_BENCHMARK = "run_query_benchmark"


class BenchmarkingSystemMetric(Enum):
    """
    Enumeration class for different system metrics used in CLP Bench.

    This class defines the system metrics that are measured during benchmarking, providing a
    standardized way to reference each metric along with its unit.

    TODO: We are planning to add CPU metric anon.

    Attributes:
        MEMORY
            Represents memory usage, measured in kilobytes (KB).
    """

    MEMORY = ("memory", "B")


class BenchmarkingResult:
    """
    Data structure to store and format benchmarking results for visualization.

    This class encapsulates various benchmarking results, such as file sizes, compression ratios,
    and latency measurements, as well as system metrics collected during benchmarking stages. It
    provides methods for formatting size and latency values for display.

    Attributes:
        SIZE_PRECISION : int
            Precision for displaying file sizes, in megabytes (MB).
        TIME_PRECISION : int
            Precision for displaying latency, in milliseconds (ms).

    Instance Attributes:
        mode : str
            The benchmarking mode associated with this result.
        compressed_size : str
            The compressed file size, formatted as a string.
        decompressed_size : str
            The decompressed file size, formatted as a string.
        ratio : str
            The compression ratio, formatted as a string.
        ingest_e2e_latency : str
            The end-to-end latency for ingestion, formatted as a string.
        query_e2e_latencies : List[str])
            A list of latency values for each query execution in the benchmarking run.
        system_metric_results : Dict[BenchmarkingSystemMetric, SystemMetricResult]
            A dictionary holding system metric results for different benchmarking stages.

    Methods:
        format_size_result(byte: int) -> str
            Formats the size from bytes to a human-readable string with the specified precision.

        format_latency_result(ns: int) -> str
            Formats the latency from nanoseconds to milliseconds with the specified precision.

    Inner Classes:
        SystemMetricResult
            A helper class to store system metric results for each benchmarking stage.
    """

    # Used for file size and memory usage, unit: MB
    SIZE_PRECISION: int = 0
    # Used for latency, unit: s
    TIME_PRECISION: int = 0

    @staticmethod
    def format_size_result(byte: int) -> str:
        """
        Formats the file size from bytes to a string with the specified
        precision.

        Args:
            byte : int
                The size in bytes.

        Returns:
            str: The formatted file size as a string with units in B.
        """

        return f"{byte}:.{BenchmarkingResult.SIZE_PRECISION}f B"

    @staticmethod
    def format_latency_result(ns: int) -> str:
        """
        Formats the latency from nanoseconds to milliseconds with the specified
        precision.

        Args:
            ns : int
                The latency in nanoseconds.

        Returns:
            str: The formatted latency as a string with units in milliseconds.
        """

        NS_TO_MS = 1 / 1e6
        return f"{(ns * NS_TO_MS):.{BenchmarkingResult.TIME_PRECISION}f} ms"

    def __init__(
        self, mode: str, compressed_size="", decompressed_size="", ratio="", ingest_e2e_latency=""
    ):
        self.mode: str = mode
        self.compressed_size: str = compressed_size
        self.decompressed_size: str = decompressed_size
        self.ratio: str = ratio
        self.ingest_e2e_latency: str = ingest_e2e_latency
        self.query_e2e_latencies = []

        class SystemMetricResult:
            """
            Helper class to store system metric results for each stage of
            benchmarking.

            Attributes:
                metric : BenchmarkingSystemMetric
                    The metric being tracked (e.g., memory).
                stage_results : Dict[BenchmarkingStage, List]
                    A dictionary mapping each stage to a list of metric values.
            """

            def __init__(self, metric: BenchmarkingSystemMetric):
                self.metric = metric
                self.stage_results: Dict[BenchmarkingStage, List] = {}
                for stage in BenchmarkingStage:
                    self.stage_results[stage] = []

        self.system_metric_results: Dict[BenchmarkingSystemMetric, SystemMetricResult] = {}
        for metric in BenchmarkingSystemMetric:
            self.system_metric_results[metric] = SystemMetricResult(metric)


class BenchmarkingEssentials:
    """
    Data structure for storing essential benchmarking environment information
    related to container operations.

    This class holds common information required for benchmarking in a containerized environment,
    including paths to scripts for various stages of the benchmarking process and the container ID.
    It verifies the existence of each required script path within the container to ensure that
    all dependencies are available for execution.

    Attributes:
        container_id : str
            The ID of the Docker container where benchmarking is performed.
        reset_script_path : str
            Path to the script that resets the container environment.
        launch_script_path : str
            Path to the script that launches the benchmarking process.
        measure_decompressed_size_script_path : str
            Path to the script that measures the decompressed dataset size.
        ingest_script_path : str
            Path to the script that ingests data into the system.
        measure_compressed_size_script_path : str
            Path to the script that measures the compressed dataset size.
        clear_cache_script_path : str
            Path to the script that clears the system's cache.
        search_script_path : str
            Path to the script that performs search queries in the benchmarking process.
        terminate_script_path : str
            Path to the script that terminates the benchmarking process.
        datasets_path : str
            Path to the datasets used for benchmarking.

    Methods:
        __check_path(script_path: str)
            Checks if the given script path exists within the container and logs its status.
    """

    def __init__(
        self,
        container_id: str,
        reset_script_path: str,
        launch_script_path: str,
        measure_decompressed_size_script_path: str,
        ingest_script_path: str,
        measure_compressed_size_script_path: str,
        clear_cache_script_path: str,
        search_script_path: str,
        terminate_script_path: str,
        datasets_path: str,
    ):
        self.container_id = container_id
        self.reset_script_path = reset_script_path
        self.__check_path(reset_script_path)
        self.launch_script_path = launch_script_path
        self.__check_path(launch_script_path)
        self.measure_decompressed_size_script_path = measure_decompressed_size_script_path
        self.__check_path(measure_decompressed_size_script_path)
        self.ingest_script_path = ingest_script_path
        self.__check_path(ingest_script_path)
        self.measure_compressed_size_script_path = measure_compressed_size_script_path
        self.__check_path(measure_compressed_size_script_path)
        self.clear_cache_script_path = clear_cache_script_path
        self.__check_path(clear_cache_script_path)
        self.search_script_path = search_script_path
        self.__check_path(search_script_path)
        self.terminate_script_path = terminate_script_path
        self.__check_path(terminate_script_path)
        self.datasets_path = datasets_path

    def __check_path(self, script_path: str):
        """
        Checks if a script path exists in the container and logs the result.

        For all scripts we need to check if they are there. Note that since datasets_path could
        also be pattern, we don't check its existence.

        Args:
            script_path : str
                The path of the script to check.

        Raises:
            Exception: If the script does not exist in the container.
        """

        try:
            subprocess.run(
                f"docker exec {self.container_id} test -e {script_path}",
                shell=True,
                check=True,
            )
            logger.info(f"{script_path} exists in container {self.container_id}")
        except subprocess.CalledProcessError:
            raise Exception(f"{script_path} does not exist in container {self.container_id}")


class BenchmarkingSystemMetricPoller:
    """
    Handles polling of system metrics during different stages of benchmarking.

    This class manages a separate thread to periodically poll a specific system metric (e.g.,
    memory usage) for each stage of the benchmarking process. Each stage has its own polling
    interval and event to control when polling should be active.

    Attributes:
        metric : BenchmarkingSystemMetric
            The system metric being tracked (e.g., memory).
        thread : threading.Thread
            The thread responsible for polling the metric.
        stage_alteration_notifier : threading.Event
            Event used to notify when the stage changes, signaling the polling thread to adjust
            behavior accordingly.
        stage_polling_intervals : Dict[BenchmarkingStage, int]
            Dictionary mapping each benchmarking stage to its polling interval, in seconds.
        stage_events : Dict[BenchmarkingStage, threading.Event]
            Dictionary mapping each benchmarking stage to an event that controls the polling
            activity during that stage.
    """

    def __init__(self, metric: BenchmarkingSystemMetric):
        self.metric = metric
        self.thread: threading.Thread = None
        self.stage_alteration_notifier = threading.Event()
        self.stage_polling_intervals: Dict[BenchmarkingStage, int] = {}
        self.stage_events: Dict[BenchmarkingStage, threading.Event] = {}
        for stage in BenchmarkingStage:
            self.stage_polling_intervals[stage] = 10
            self.stage_events[stage] = threading.Event()


class ClpBenchExecutor:
    """
    Executor class for managing and executing benchmarking tasks in CLP Bench.

    This class is responsible for setting up, executing, and collecting results for benchmarking
    processes in a containerized environment. It includes methods for launching, ingesting data,
    running queries, and visualizing results. Additionally, it manages system metric polling
    for each benchmarking stage and mode.

    Attributes:
        __benchmarking_essentials : BenchmarkingEssentials
            Stores essential configuration and script paths.
        __queries : List[str]
            List of queries to be executed during benchmarking.
        __hot_run_warm_up_times : int
            Number of warm-up runs for hot-run mode.
        __related_processes : List[str]
            List of related processes for monitoring metrics.
        __system_metric_enable : bool
            Flag indicating whether system metric polling is enabled.
        __system_metric_pollers : Dict[BenchmarkingSystemMetric, BenchmarkingSystemMetricPoller]
            Dictionary of pollers for each system metric.
        __benchmarking_results : Dict[BenchmarkingMode, BenchmarkingResult]
            Stores results for each mode.
        __overall_threading_event : threading.Event
            Event to control the start and stop of metric polling.

    Methods:
        launch(mode: BenchmarkingMode)
            Launches the benchmarking process in the specified mode.

        terminate(mode: BenchmarkingMode)
            Terminates the benchmarking process in the specified mode.

        ingest(mode: BenchmarkingMode)
            Runs the ingestion phase and measures compressed and decompressed sizes, as well as
            latency.

        run_query_benchmark(mode: BenchmarkingMode)
            Executes query benchmarks and records end-to-end latency for each query.

        visualize()
            Logs the benchmarking results for each mode, including sizes, ratios, and latencies.

        start_polling_system_metric(metric: BenchmarkingSystemMetric, mode: BenchmarkingMode)
            Starts a polling thread to monitor the specified metric in the given mode.

        stop_polling_system_metric(metric: BenchmarkingSystemMetric, mode: BenchmarkingMode)
            Stops the polling thread for the specified metric in the given mode.

        __load_benchmarking_essentials_config(assets_path: str)
            Loads and configures the benchmarking essentials from a YAML configuration file.

        __set_thread_event_for_stage(stage: BenchmarkingStage)
            Sets or clears events for each benchmarking stage based on the current stage.

        __execute_script(script_path: str, args: List[str] = [])
            Executes a script in the Docker container and returns its output.

        __record_system_metric_polling_sample(
            metric: BenchmarkingSystemMetric,
            mode: BenchmarkingMode
        )
            Records a polling sample for a specified system metric during a benchmarking stage.

        __acquire_system_metric_sample(metric: BenchmarkingSystemMetric) -> int
            Acquires a sample for the specified system metric from the container.

        __poll_system_metrics(metric: BenchmarkingSystemMetric, mode: BenchmarkingMode)
            Continuously polls the specified system metric while benchmarking is active.
    """

    def __init__(self, assets_path: str) -> None:
        super().__init__()
        self.__benchmarking_essentials: BenchmarkingEssentials
        self.__queries: List[str]
        self.__hot_run_warm_up_times: int
        self.__related_processes: List[str]
        self.__system_metric_enable: bool
        self.__system_metric_pollers: Dict[BenchmarkingSystemMetric, BenchmarkingSystemMetricPoller]
        self.__load_benchmarking_essentials_config(assets_path)
        # Results for different modes
        self.__benchmarking_results: Dict[BenchmarkingMode, BenchmarkingResult] = {}
        for mode in BenchmarkingMode:
            self.__benchmarking_results[mode] = BenchmarkingResult(mode)

        self.__overall_threading_event = threading.Event()

    def launch(self, mode: BenchmarkingMode):
        """
        Launches the benchmarking process for the specified mode.

        Args:
            mode : BenchmarkingMode
                The mode to launch (e.g., INGEST_MODE).
        """
        self.__execute_script(self.__benchmarking_essentials.launch_script_path)
        if BenchmarkingMode.INGEST_MODE == mode:
            self.__execute_script(self.__benchmarking_essentials.reset_script_path)

    def terminate(self, mode: BenchmarkingMode):
        """
        Terminates the benchmarking process for the specified mode.

        Args:
            mode : BenchmarkingMode
                The mode to terminate.
        """
        self.__execute_script(self.__benchmarking_essentials.terminate_script_path)

    def ingest(self, mode: BenchmarkingMode):
        """
        Runs the ingestion phase, recording compressed and decompressed sizes
        and latency.

        Args:
            mode : BenchmarkingMode
                The benchmarking mode for which ingestion is run.
        """
        self.__set_thread_event_for_stage(BenchmarkingStage.INGEST)
        self.__benchmarking_results[mode].decompressed_size = BenchmarkingResult.format_size_result(
            int(
                self.__execute_script(
                    self.__benchmarking_essentials.measure_decompressed_size_script_path,
                    [self.__benchmarking_essentials.datasets_path],
                )
            )
        )
        start_ts = time.perf_counter_ns()
        self.__execute_script(
            self.__benchmarking_essentials.ingest_script_path,
            [self.__benchmarking_essentials.datasets_path],
        )
        end_ts = time.perf_counter_ns()
        self.__benchmarking_results[mode].compressed_size = BenchmarkingResult.format_size_result(
            int(
                self.__execute_script(
                    self.__benchmarking_essentials.measure_compressed_size_script_path
                )
            )
        )
        self.__benchmarking_results[mode].ingest_e2e_latency = (
            BenchmarkingResult.format_latency_result(end_ts - start_ts)
        )

    def run_query_benchmark(self, mode: BenchmarkingMode):
        """
        Runs the query benchmarking phase and records end-to-end latencies for
        each query.

        Args:
            mode : BenchmarkingMode
                The benchmarking mode for which query benchmarking is run.
        """
        self.__set_thread_event_for_stage(BenchmarkingStage.RUN_QUERY_BENCHMARK)
        for query in self.__queries:
            if BenchmarkingMode.COLD_RUN_MODE == mode:
                logger.info("Clearing page cache")
                self.__execute_script(self.__benchmarking_essentials.clear_cache_script_path)
            elif BenchmarkingMode.HOT_RUN_MODE == mode:
                for i in range(self.__hot_run_warm_up_times):
                    self.__execute_script(
                        self.__benchmarking_essentials.search_script_path, [query]
                    )
            start_ts = time.perf_counter_ns()
            query_result = self.__execute_script(
                self.__benchmarking_essentials.search_script_path, [query]
            )
            end_ts = time.perf_counter_ns()
            nr_matched_log_lines = int(query_result)
            logger.info(f"Number of matched log lines: {nr_matched_log_lines}")
            self.__benchmarking_results[mode].query_e2e_latencies.append(
                BenchmarkingResult.format_latency_result(end_ts - start_ts)
            )

    def visualize(self):
        """
        Logs the benchmarking results for each mode, including
        decompressed/compressed sizes, ratios, ingestion latency, and query
        latencies.
        """
        for mode, result in self.__benchmarking_results.items():
            if result.decompressed_size:
                logger.info(
                    f"{mode.value.capitalize()} mode: decompressed size "
                    f"{result.decompressed_size}"
                )
            if result.compressed_size:
                logger.info(
                    f"{mode.value.capitalize()} mode: " f"compressed size {result.compressed_size}"
                )
            if result.ratio:
                logger.info(f"{mode.value.capitalize()} mode: " f"compression ratio {result.ratio}")
            if result.ingest_e2e_latency:
                logger.info(
                    f"{mode.value.capitalize()} mode: ingest e2e latency "
                    f"{result.ingest_e2e_latency}"
                )
            for i in range(len(result.query_e2e_latencies)):
                logger.info(
                    f"{mode.value.capitalize()} mode: No.{i} query e2e latency "
                    f"{result.query_e2e_latencies[i]}"
                )

            if self.__system_metric_enable:
                for metric in BenchmarkingSystemMetric:
                    for stage in BenchmarkingStage:
                        if not result.system_metric_results[metric].stage_results[stage]:
                            average_metric_result = 0
                        else:
                            result.system_metric_results[metric].stage_results[stage] = [
                                result
                                for result in result.system_metric_results[metric].stage_results[
                                    stage
                                ]
                                if 0 < result
                            ]
                            average_metric_result = int(
                                statistics.mean(
                                    result.system_metric_results[metric].stage_results[stage]
                                )
                            )
                            logger.info(
                                f"{mode.value.capitalize()} mode: average {metric.value[0]} usage "
                                f"at {stage.value} stage: {average_metric_result} {metric.value[1]}"
                            )

    def start_polling_system_metric(self, metric: BenchmarkingSystemMetric, mode: BenchmarkingMode):
        """
        Starts a polling thread for monitoring the specified system metric in
        the given mode.

        Args:
            metric : BenchmarkingSystemMetric
                The system metric to monitor.
            mode : BenchmarkingMode
                The mode in which the polling should be activated.
        """
        if not self.__system_metric_enable:
            return
        if not self.__overall_threading_event.is_set():
            logger.info(f"Start polling {metric.value[0]} usage for mode {mode.value}")
            self.__overall_threading_event.set()
            self.__system_metric_pollers[metric].thread = threading.Thread(
                target=self.__poll_system_metrics,
                args=(
                    metric,
                    mode,
                ),
                daemon=True,
            )
            self.__system_metric_pollers[metric].thread.start()
        else:
            logger.error(f"Already being polling {metric.value[0]} usage for mode {mode.value}")

    def stop_polling_system_metric(self, metric: BenchmarkingSystemMetric, mode: BenchmarkingMode):
        """
        Stops the polling thread for the specified system metric in the given
        mode.

        Args:
            metric : BenchmarkingSystemMetric
                The system metric to stop monitoring.
            mode : BenchmarkingMode
                The mode for which the polling should be stopped.
        """
        if not self.__system_metric_enable:
            return
        if self.__overall_threading_event.is_set():
            logger.info(f"Stop polling {metric.value[0]} usage for mode {mode.value}")
            self.__overall_threading_event.clear()
        else:
            logger.error(f"Already stopped polling {metric.value[0]} usage for mode {mode.value}")

    def __load_benchmarking_essentials_config(self, assets_path: str):
        """
        Loads and configures the benchmarking essentials from a YAML
        configuration file.

        This method reads configuration details from `config.yaml` located in the specified assets
        path, and initializes `BenchmarkingEssentials` and other parameters required for
        benchmarking.

        Args:
            assets_path : str
                The path to the directory containing the `config.yaml` configuration file.

        Raises:
            Exception: If the configuration file cannot be parsed or essential configurations are
            missing.
        """
        config_path = f"{assets_path}/config.yaml"
        with open(config_path, "r") as config_file:
            config = yaml.safe_load(config_file)
            if config is None:
                raise Exception("Unable to parse " + config_path)
        assets_path_in_container = config["assets_path"]
        self.__benchmarking_essentials = BenchmarkingEssentials(
            config["container_id"],
            f"{assets_path_in_container}/reset_script",
            f"{assets_path_in_container}/launch_script",
            f"{assets_path_in_container}/measure_decompressed_size_script",
            f"{assets_path_in_container}/ingest_script",
            f"{assets_path_in_container}/measure_compressed_size_script",
            f"{assets_path_in_container}/clear_cache_script",
            f"{assets_path_in_container}/search_script",
            f"{assets_path_in_container}/terminate_script",
            config["datasets_path"],
        )
        self.__queries: List[str] = config["queries"]
        self.__hot_run_warm_up_times: int = config.get("hot_run_warm_up_times", 3)
        self.__related_processes: List[str] = config["related_processes"]
        self.__system_metric_pollers = {}
        self.__system_metric_enable = config.get("system_metric", {}).get("enable", False)
        for metric in BenchmarkingSystemMetric:
            self.__system_metric_pollers[metric] = BenchmarkingSystemMetricPoller(metric)
        for stage in BenchmarkingStage:
            for metric in BenchmarkingSystemMetric:
                interval = (
                    config.get("system_metric", {})
                    .get(metric.value[0], {})
                    .get(f"{stage.value}_polling_interval", 10)
                )
                self.__system_metric_pollers[metric].stage_polling_intervals[stage] = interval
                logger.info(
                    f"{metric.value[0].capitalize()} usage polling interval for {stage.value}: "
                    f"{interval} seconds"
                )

    def __set_thread_event_for_stage(self, stage: BenchmarkingStage):
        """
        Sets or clears events for each benchmarking stage based on the current
        stage.

        Args:
            stage : BenchmarkingStage
                The current stage for which events are to be set.
        """
        for it_stage in BenchmarkingStage:
            for it_metric in BenchmarkingSystemMetric:
                if stage != it_stage:
                    self.__system_metric_pollers[it_metric].stage_events[it_stage].clear()
                else:
                    self.__system_metric_pollers[it_metric].stage_events[it_stage].set()
                    self.__system_metric_pollers[it_metric].stage_alteration_notifier.set()
                    self.__system_metric_pollers[it_metric].stage_alteration_notifier.clear()

    def __execute_script(self, script_path: str, args: List[str] = []) -> str:
        """
        Executes a script in the Docker container and returns its output.

        Args:
            script_path : str
                Path to the script to be executed in the container.
            args : List[str], optional
                Additional arguments for the script. Defaults to an empty list.

        Returns:
            str: Output from the script execution.

        Raises:
            subprocess.CalledProcessError: If the script execution fails.
        """
        try:
            logger.info(
                f"Executing script@{script_path} in container: "
                f"{self.__benchmarking_essentials.container_id}"
            )
            command = f"docker exec {self.__benchmarking_essentials.container_id} {script_path}"
            for arg in args:
                command += f" {arg}"
            result = subprocess.run(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, check=True
            )
            logger.debug(result)
            return result.stdout.decode("utf-8").strip()
        except subprocess.CalledProcessError as e:
            logger.error(
                f"Failed to execute script@{script_path} in container: "
                f"{self.__benchmarking_essentials.container_id}"
            )
            raise e

    def __record_system_metric_polling_sample(
        self, metric: BenchmarkingSystemMetric, mode: BenchmarkingMode
    ):
        """
        Records a polling sample for a specified system metric during a
        benchmarking stage.

        This method captures a sample of the specified metric (e.g., memory usage) if the
        event for the current stage is set, and appends the sample to the benchmarking results
        for the specified mode and stage.

        Args:
            metric : BenchmarkingSystemMetric
                The system metric being polled.
            mode : BenchmarkingMode
                The benchmarking mode for which the metric is being recorded.

        Note:
            Only one stage's event should be set at any given time, and the method will wait for
            the next polling interval before continuing.
        """
        for stage in BenchmarkingStage:
            if self.__system_metric_pollers[metric].stage_events[stage].is_set():
                metric_sample = self.__acquire_system_metric_sample(metric)
                if 0 >= metric_sample:
                    break
                self.__benchmarking_results[mode].system_metric_results[metric].stage_results[
                    stage
                ].append(metric_sample)
                logger.info(
                    f"Current {metric.value[0]} usage at {stage.value} stage: {metric_sample}"
                    f" {metric.value[1]}"
                )
                self.__system_metric_pollers[metric].stage_alteration_notifier.wait(
                    self.__system_metric_pollers[metric].stage_polling_intervals[stage]
                )
                break  # Only one stage's event should be set at any time

    def __acquire_system_metric_sample(self, metric: BenchmarkingSystemMetric) -> int:
        """
        Acquires a sample for the specified system metric from the container.

        This method executes a command in the Docker container to capture the specified metric
        (e.g., memory usage), which is used for performance monitoring.

        Args:
            metric : BenchmarkingSystemMetric
                The system metric to acquire.

        Returns:
            int: The sample value of the metric, in bytes if it's memory.

        Raises:
            Exception: If the metric is unknown or unsupported.
        """
        if BenchmarkingSystemMetric.MEMORY == metric:
            KB_TO_B = 1024
            result = subprocess.run(
                f"docker exec {self.__benchmarking_essentials.container_id} ps aux",
                stdout=subprocess.PIPE,
                shell=True,
                check=True,
            )
            output = result.stdout.decode("utf-8").strip().split("\n")
            metric_sample = 0
            for line in output:
                process = line.strip().split()[10].strip()
                flag = False
                for related_process in self.__related_processes:
                    if related_process.startswith(process):
                        flag = True
                        break
                if flag:
                    metric_sample += int(line.strip().split()[5]) * KB_TO_B
            return metric_sample
        else:
            raise Exception(f"Unknown metric: {metric.value[0]}")

    def __poll_system_metrics(self, metric: BenchmarkingSystemMetric, mode: BenchmarkingMode):
        """
        Continuously polls the specified system metric while benchmarking is
        active.

        This method runs in a separate thread, polling the specified metric at regular intervals
        as long as the `__overall_threading_event` is set, and records each sample.

        Args:
            metric : BenchmarkingSystemMetric
                The system metric to poll.
            mode : BenchmarkingMode
                The benchmarking mode in which the metric is being polled.
        """
        while self.__overall_threading_event.is_set():
            self.__record_system_metric_polling_sample(metric, mode)

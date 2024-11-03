import logging
import statistics
import subprocess
import threading
import time
from enum import Enum
from typing import Dict, List

import yaml

# Retrieve logger
logger = logging.getLogger(__name__)


class BenchmarkingMode(Enum):
    """
    Benchmarking mode marcos.
    """

    HOT_RUN_MODE = "hot run"
    COLD_RUN_MODE = "cold run"
    QUERY_ONLY_RUN_MODE = "query only run"
    INGEST_MODE = "ingest"


class BenchmarkingStage(Enum):
    """
    Benchmarking stage marcos
    """

    INGEST = "ingest"
    RUN_QUERY_BENCHMARK = "run_query_benchmark"


class BenchmarkingSystemMetric(Enum):
    """
    Benchmarking system metric marcos
    """

    MEMORY = ("memory", "KB")


class BenchmarkingResult:
    """
    Benchmarking result data structure, for visualization.
    """

    # Used for file size and memory usage, unit: MB
    SIZE_PRECISION: int = 2
    # Used for latency, unit: s
    TIME_PRECISION: int = 9
    # Indicate the system metric does not have baseline
    NO_REQUIRE_BASELINE_SYSTEM_METRIC: int = -1
    # Indicate the system metric needs baseline
    REQUIRE_BASELINE_SYSTEM_METRIC: int = 0

    @staticmethod
    def get_mb_from_byte(byte: int) -> str:
        BYTES_TO_MB = 1 / 1024 / 1024
        return f"{(byte * BYTES_TO_MB):.{BenchmarkingResult.SIZE_PRECISION}f} MB"

    @staticmethod
    def get_s_from_ns(ns: int) -> str:
        NS_TO_S = 1 / 1e9
        return f"{(ns * NS_TO_S):.{BenchmarkingResult.TIME_PRECISION}f} s"

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
            def __init__(self, metric: BenchmarkingSystemMetric):
                self.metric = metric
                self.result_baseline = BenchmarkingResult.NO_REQUIRE_BASELINE_SYSTEM_METRIC
                self.stage_results: Dict[BenchmarkingStage, List] = {}
                for stage in BenchmarkingStage:
                    self.stage_results[stage] = []

        self.system_metric_results: Dict[BenchmarkingSystemMetric, SystemMetricResult] = {}
        for metric in BenchmarkingSystemMetric:
            self.system_metric_results[metric] = SystemMetricResult(metric)


class BenchmarkingEssentials:
    """
    Benchmarking environment data structure, stores the common information of the container
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
        self.__check_path(datasets_path)

    def __check_path(self, script_path: str):
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
    Namespace for all essential CPT workflow steps. A base class.

    Different tools that to be benchmarked might need to implement
    their own executor based on this base class, which works in a
    SPI manner.
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

    # The following are some utils
    def _check_file_in_docker(self, container_id: str, file_path: str) -> None:
        try:
            subprocess.run(["docker", "exec", container_id, "test", "-f", file_path], check=True)
            logger.info(f"{file_path} exists in container {container_id}")
        except subprocess.CalledProcessError:
            raise Exception(f"{file_path} does not exist in container {container_id}")

    def _check_directory_in_docker(
        self, container_id: str, directory_path: str, need_to_create=True, need_to_clear=False
    ) -> None:
        try:
            subprocess.run(
                ["docker", "exec", container_id, "test", "-d", directory_path], check=True
            )
            logger.info(f"{directory_path} exists in {container_id}")
            if need_to_clear:
                logger.info(
                    f"Clearing existing stuff in {directory_path} in container {container_id}"
                )
                try:
                    # Note to myself: when running the command manually in a shell, the wildcard
                    # (*) is expanded by the shell to match files in the directory. However, when
                    # you run it through `subprocess.run`, there is no shell involved by default,
                    # so the wildcard (*) isn’t expanded and remains a literal *, which won’t work
                    # as expected. So the solution is to use `bash -c` to enable wildcard
                    # expansion.
                    subprocess.run(
                        [
                            "docker",
                            "exec",
                            container_id,
                            "bash",
                            "-c",
                            f"rm -rf {directory_path}/*",
                        ],
                        check=True,
                    )
                    logger.info(
                        f"All contents within {directory_path} cleared successfully in container "
                        f"{container_id}"
                    )
                except subprocess.CalledProcessError as e:
                    raise Exception(
                        f"Failed to clear {directory_path} contents in {container_id}: {e}"
                    )
        except subprocess.CalledProcessError as e1:
            if need_to_create:
                logger.info(f"{directory_path} does not exist in {container_id}, try to create one")
                try:
                    subprocess.run(
                        ["docker", "exec", container_id, "mkdir", "-p", directory_path], check=True
                    )
                    logger.info(
                        f"{directory_path} created successfully in container {container_id}"
                    )
                except subprocess.CalledProcessError as e2:
                    raise Exception(
                        f"{directory_path} failed to create in container {container_id}: {e2}"
                    )
            else:
                raise Exception(f"{directory_path} does not exist in {container_id}: {e1}")

    def __set_thread_event_for_stage(self, stage: BenchmarkingStage):
        for it_stage in BenchmarkingStage:
            for it_metric in BenchmarkingSystemMetric:
                if stage != it_stage:
                    self.__system_metric_pollers[it_metric].stage_events[it_stage].clear()
                else:
                    self.__system_metric_pollers[it_metric].stage_events[it_stage].set()
                    self.__system_metric_pollers[it_metric].stage_alteration_notifier.set()
                    self.__system_metric_pollers[it_metric].stage_alteration_notifier.clear()

    def __execute_script(self, script_path: str, args: List[str] = []) -> str:
        try:
            logger.info(
                f"Executing script@{script_path} in container: {self.__benchmarking_essentials.container_id}"
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
                f"Failed to execute script@{script_path} in container: {self.__benchmarking_essentials.container_id}"
            )
            raise e

    def launch(self, mode: BenchmarkingMode):
        self.__execute_script(self.__benchmarking_essentials.launch_script_path)
        if BenchmarkingMode.INGEST_MODE == mode:
            self.__execute_script(self.__benchmarking_essentials.reset_script_path)

    def terminate(self, mode: BenchmarkingMode):
        self.__execute_script(self.__benchmarking_essentials.terminate_script_path)

    def ingest(self, mode: BenchmarkingMode):
        self.__set_thread_event_for_stage(BenchmarkingStage.INGEST)
        self.__benchmarking_results[mode].decompressed_size = BenchmarkingResult.get_mb_from_byte(
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
        self.__benchmarking_results[mode].compressed_size = BenchmarkingResult.get_mb_from_byte(
            int(
                self.__execute_script(
                    self.__benchmarking_essentials.measure_compressed_size_script_path
                )
            )
        )
        self.__benchmarking_results[mode].ingest_e2e_latency = BenchmarkingResult.get_s_from_ns(
            end_ts - start_ts
        )

    def run_query_benchmark(self, mode: BenchmarkingMode):
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
                BenchmarkingResult.get_s_from_ns(end_ts - start_ts)
            )

    def visualize(self):
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
                            if (
                                BenchmarkingResult.NO_REQUIRE_BASELINE_SYSTEM_METRIC
                                != result.system_metric_results[metric].result_baseline
                            ):
                                average_metric_result = int(
                                    statistics.mean(
                                        result.system_metric_results[metric].stage_results[stage]
                                    )
                                    - result.system_metric_results[metric].result_baseline
                                )
                            else:
                                average_metric_result = int(
                                    statistics.mean(
                                        result.system_metric_results[metric].stage_results[stage]
                                    )
                                )
                            logger.info(
                                f"{mode.value.capitalize()} mode: average {metric.value[0]} usage "
                                f"at {stage.value} stage: {average_metric_result}{metric.value[1]}"
                            )

    def __load_benchmarking_essentials_config(self, assets_path: str):
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

    def __record_system_metric_polling_sample(
        self, metric: BenchmarkingSystemMetric, mode: BenchmarkingMode
    ):
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
                    f"{metric.value[1]}"
                )
                self.__system_metric_pollers[metric].stage_alteration_notifier.wait(
                    self.__system_metric_pollers[metric].stage_polling_intervals[stage]
                )
                break  # Only one stage's event should be set at any time

    def __acquire_system_metric_sample(self, metric: BenchmarkingSystemMetric) -> int:
        if BenchmarkingSystemMetric.MEMORY == metric:
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
                if process in self.__related_processes:
                    metric_sample += int(line.strip().split()[5])
            return metric_sample
        else:
            raise Exception(f"Unknown metric: {metric.value[0]}")

    def __poll_system_metrics(self, metric: BenchmarkingSystemMetric, mode: BenchmarkingMode):
        while self.__overall_threading_event.is_set():
            self.__record_system_metric_polling_sample(metric, mode)

    def start_polling_system_metric(self, metric: BenchmarkingSystemMetric, mode: BenchmarkingMode):
        if not self.__system_metric_enable:
            return
        if not self.__overall_threading_event.is_set():
            logger.info(f"Start polling {metric.value[0]} usage for mode {mode.value}")
            if (
                BenchmarkingResult.REQUIRE_BASELINE_SYSTEM_METRIC
                == self.__benchmarking_results[mode].system_metric_results[metric].result_baseline
            ):
                metric_sample = self.__acquire_system_metric_sample(metric)
                self.__benchmarking_results[mode].system_metric_results[
                    metric
                ].result_baseline = metric_sample
                logger.info(f"Initial {metric.value[0]} usage: {metric_sample}{metric.value[1]}")
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
        if not self.__system_metric_enable:
            return
        if self.__overall_threading_event.is_set():
            logger.info(f"Stop polling {metric.value[0]} usage for mode {mode.value}")
            self.__overall_threading_event.clear()
        else:
            logger.error(f"Already stopped polling {metric.value[0]} usage for mode {mode.value}")

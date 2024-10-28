import logging
import subprocess
import time

from .executor import (
    BenchmarkingMode,
    BenchmarkingResult,
    BenchmarkingSystemMetric,
    CPTExecutorBase,
)

logger = logging.getLogger(__name__)


class CPTExecutorMongoDB(CPTExecutorBase):
    """
    A service provider for clp, which is a binary; clg is used for searching.
    """

    def __init__(self, config_path: str) -> None:
        super().__init__(config_path)
        for mode in BenchmarkingMode:
            self.benchmarking_results[mode].system_metric_results[
                BenchmarkingSystemMetric.MEMORY
            ].result_baseline = BenchmarkingResult.NO_REQUIRE_BASELINE_SYSTEM_METRIC

    def deploy(self, mode: BenchmarkingMode):
        logger.info("Deploying MongoDB")
        container_id = self.config["mongodb"]["container_id"]
        logger.info(f"MongoDB docker container ID: {container_id}")
        launch_script_path = self.config["mongodb"]["launch_script_path"]
        logger.info(f"MongoDB launch script location: {launch_script_path}")
        ingest_script_path = self.config["mongodb"]["ingest_script_path"]
        logger.info(f"MongoDB compress script location: {ingest_script_path}")
        search_script_path = self.config["mongodb"]["search_script_path"]
        logger.info(f"MongoDB search script location: {search_script_path}")
        terminate_script_path = self.config["mongodb"]["terminate_script_path"]
        logger.info(f"MongoDB terminate script location: {terminate_script_path}")
        dataset_path = self.config["mongodb"]["dataset_path"]
        logger.info(f"MongoDB dataset location: {dataset_path}")

        self._check_file_in_docker(container_id, launch_script_path)
        self._check_file_in_docker(container_id, ingest_script_path)
        self._check_file_in_docker(container_id, search_script_path)
        self._check_file_in_docker(container_id, terminate_script_path)
        self._check_file_in_docker(container_id, dataset_path)

    def ingest(self, mode: BenchmarkingMode):
        super().ingest(mode)
        logger.info("Ingesting data for MongoDB")
        container_id = self.config["mongodb"]["container_id"]
        ingest_script_path = self.config["mongodb"]["ingest_script_path"]
        dataset_path = self.config["mongodb"]["dataset_path"]
        try:
            result = subprocess.run(
                f"docker exec {container_id} du {dataset_path} -c -b",
                stdout=subprocess.PIPE,
                shell=True,
                check=True,
            )
            self.benchmarking_results[mode].decompressed_size = BenchmarkingResult.get_mb_from_byte(
                int(result.stdout.decode("utf-8").split("\n")[-2].split()[0].strip())
            )
            start_ts = time.perf_counter_ns()
            subprocess.run(
                f"docker exec {container_id} bash {ingest_script_path} {dataset_path}",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
                shell=True,
                check=True,
            )
            end_ts = time.perf_counter_ns()
            self.benchmarking_results[mode].ingest_e2e_latency = BenchmarkingResult.get_s_from_ns(
                end_ts - start_ts
            )
            time.sleep(10)
            result = subprocess.run(
                f"docker exec {container_id} bash {ingest_script_path} --size-only",
                stdout=subprocess.PIPE,
                shell=True,
                check=True,
            )
            self.benchmarking_results[mode].compressed_size = BenchmarkingResult.get_mb_from_byte(
                int(result.stdout.decode("utf-8").strip())
            )
        except subprocess.CalledProcessError as e:
            raise Exception(f"MongoDB failed to ingest: {e}")

    def run_query_benchmark(self, mode: BenchmarkingMode):
        super().run_query_benchmark(mode)
        logger.info("Running query benchmark for MongoDB")
        container_id = self.config["mongodb"]["container_id"]
        search_script_path = self.config["mongodb"]["search_script_path"]
        queries = self.config["mongodb"]["queries"]
        for query in queries:
            if BenchmarkingMode.COLD_RUN_MODE == mode:
                logger.info("Clearing page cache")
                subprocess.run(
                    f"docker exec {container_id} sh -c 'sync; echo 1 > /proc/sys/vm/drop_caches'",
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.STDOUT,
                    shell=True,
                    check=True,
                )
            command = f"docker exec {container_id} bash {search_script_path} '{query}'"
            self._execute_query(mode, command)

    def mid_terminate(self, mode: BenchmarkingMode):
        super().mid_terminate(mode)
        self.terminate(mode)

    def launch(self, mode: BenchmarkingMode):
        logger.info("Launching MongoDB")
        container_id = self.config["mongodb"]["container_id"]
        launch_script_path = self.config["mongodb"]["launch_script_path"]
        try:
            if BenchmarkingMode.INGEST_MODE == mode:
                command = f"docker exec {container_id} bash {launch_script_path} --drop-if-existed"
            else:
                command = f"docker exec {container_id} bash {launch_script_path}"
            subprocess.run(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
                shell=True,
                check=True,
            )
            time.sleep(10)
            logger.info(f"MongoDB launched successfully in container {container_id}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"MongoDB failed to launch: {e}")

    def terminate(self, mode: BenchmarkingMode):
        logger.info("Terminating MongoDB")
        container_id = self.config["mongodb"]["container_id"]
        terminate_script_path = self.config["mongodb"]["terminate_script_path"]
        try:
            subprocess.run(
                f"docker exec {container_id} bash {terminate_script_path}",
                shell=True,
                check=True,
            )
            logger.info(f"MongoDB terminated successfully in container {container_id}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"MongoDB failed to terminate: {e}")

    def _acquire_system_metric_sample(self, metric: BenchmarkingSystemMetric) -> int:
        container_id = self.config["mongodb"]["container_id"]
        try:
            command = f"docker exec {container_id} ps aux"
            result = subprocess.run(command, stdout=subprocess.PIPE, shell=True, check=True)
            output = result.stdout.decode("utf-8").strip().split("\n")
            metric = 0
            mongodb_related_command = (
                "mongod",
                "mongoimport",
                "mongosh",
                "mongoexport",
            )
            for line in output:
                commnad_header = line.strip().split()[10].strip()
                if commnad_header in mongodb_related_command:
                    metric += int(line.strip().split()[5])
            return metric
        except subprocess.CalledProcessError:
            raise Exception("MongoDB failed to get mem usage info")

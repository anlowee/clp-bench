import logging
import subprocess

from .executor import BenchmarkingMode, BenchmarkingSystemMetric, CPTExecutorBase, BenchmarkingResult

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
        self._check_directory_in_docker(container_id, dataset_path, need_to_create=False)
        

    def ingest(self, mode: BenchmarkingMode):
        super().ingest(mode)
        logger.info("Ingesting data for MongoDB")
        container_id = self.config["mongodb"]["container_id"]
        ingest_script_path = self.config["mongodb"]["ingest_script_path"]
        dataset_path = self.config["mongodb"]["dataset_path"]
        try:
            subprocess.run(
                f"docker exec {container_id} bash {ingest_script_path}"
            )
        

    def run_query_benchmark(self, mode: BenchmarkingMode):
        super().run_query_benchmark(mode)
        logger.info("Running query benchmark for MongoDB")
        container_id = self.config["mongodb"]["container_id"]
        search_script_path = self.config["mongodb"]["search_script_path"]
        queries = self.config["mongodb"]["queries"]
        for query in queries:
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
            subprocess.run(
                ["docker", "exec", container_id, "bash", "-c", f"bash {launch_script_path}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
                check=True,
            )
            logger.info(f"MongoDB launched successfully in container {container_id}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"MongoDB failed to launch: {e}")


    def terminate(self, mode: BenchmarkingMode):
        logger.info("Terminating MongoDB")
        container_id = self.config["mongodb"]["container_id"]
        terminate_script_path = self.config["mongodb"]["terminate_script_path"]
        try:
            subprocess.run(
                ["docker", "exec", container_id, "bash", "-c", f"bash {terminate_script_path}"],
                check=True,
            )
            logger.info(f"MongoDB terminated successfully in container {container_id}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"MongoDB failed to terminate: {e}")

    

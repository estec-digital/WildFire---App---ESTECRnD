import logging
import os
import sys

class LoggerSetup:
    def __init__(self, log_filename="Logs/DATA_AI_ENGINE_service.log"):
        self.log_filename = log_filename
        self._setup_logger()

    def _setup_logger(self):
        os.makedirs(os.path.dirname(self.log_filename), exist_ok=True)

        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        # Clear old handlers
        if logger.hasHandlers():
            logger.handlers.clear()

        # Console & file handlers
        console_handler = logging.StreamHandler(sys.stdout)
        file_handler = logging.FileHandler(self.log_filename, encoding="utf-8", mode='a')

        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        self.logger = logger

    def get_logger(self):
        return self.logger

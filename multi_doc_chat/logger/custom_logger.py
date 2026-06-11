import logging
from datetime import datetime
import os
import structlog


class CustomLogger:
    def __init__(self, log_dir="logs"):
        self.log_dir = os.path.join(os.getcwd(), log_dir)
        os.makedirs(self.log_dir, exist_ok=True)
        
        log_file = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
        self.log_file_path = os.path.join(self.log_dir, log_file)
        
    def get_logger(self,name=__file__):
        logger_name = os.path.basename(name)
        
        file_handler = logging.FileHandler(self.log_file_path)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(message)s'))
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter('%(message)s'))
        
        logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[file_handler, console_handler])
        
        structlog.configure(
            processors=[
                structlog.processors.KeyValueRenderer(key_order=["event", "timestamp"])
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        return structlog.get_logger(logger_name)
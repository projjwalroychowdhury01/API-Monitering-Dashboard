import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict

class StructuredLogger:
    """
    A structured JSON logger for microservices.
    Ensures logs are consistent across all services for easier log aggregation.
    """
    def __init__(self, service_name: str, level: int = logging.INFO):
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(level)
        
        # Avoid duplicate handlers if logger is re-initialized
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(level)  # Explicitly set handler level
            handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(handler)

    def _format_log(self, level: str, message: str, extra: Dict[str, Any] = None) -> str:
        # Format: timestamp | LEVEL | message
        timestamp = datetime.utcnow().isoformat()
        return f"{timestamp} | {level} | {message}"

    def info(self, message: str, extra: Dict[str, Any] = None):
        self.logger.info(self._format_log("INFO", message, extra))

    def error(self, message: str, extra: Dict[str, Any] = None):
        self.logger.error(self._format_log("ERROR", message, extra))

    def warning(self, message: str, extra: Dict[str, Any] = None):
        self.logger.warning(self._format_log("WARNING", message, extra))

    def debug(self, message: str, extra: Dict[str, Any] = None):
        self.logger.debug(self._format_log("DEBUG", message, extra))

# Shared instance for easy import
def get_logger(service_name: str) -> StructuredLogger:
    return StructuredLogger(service_name)

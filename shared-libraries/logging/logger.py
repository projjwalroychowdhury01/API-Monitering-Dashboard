import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """
    Custom formatter to output logs in a structured JSON format.
    Ideal for cloud-native log aggregators (ELK, CloudWatch, etc.)
    """
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "service": getattr(record, "service_name", "unknown"),
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno
        }
        
        # Merge extra fields if provided
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)
            
        return json.dumps(log_entry)

def get_logger(service_name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Factory function to create a configured structured logger.
    """
    logger = logging.getLogger(service_name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = JSONFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    class ServiceAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            kwargs["extra"] = kwargs.get("extra", {})
            kwargs["extra"]["service_name"] = self.extra["service_name"]
            if "extra_fields" in kwargs:
                kwargs["extra"]["extra_fields"] = kwargs.pop("extra_fields")
            return msg, kwargs

    return ServiceAdapter(logger, {"service_name": service_name})

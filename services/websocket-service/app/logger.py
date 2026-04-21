import os
import sys
from app.config import settings

# Resolve path to shared libraries relative to service root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared_libraries/python")))

try:
    from shared_logging.logger import get_logger
except ImportError:
    import logging
    def get_logger(service_name):
        return logging.getLogger(service_name)

logger = get_logger(settings.SERVICE_NAME)

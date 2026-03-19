import os
import sys
from app.config import settings

# Path to shared libraries
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared-libraries/python")))

try:
    from shared_logging.logger import get_logger
except ImportError:
    # Fallback if shared lib is not reachable during local dev without PYTHONPATH set
    import logging
    def get_logger(service_name):
        return logging.getLogger(service_name)

logger = get_logger(settings.SERVICE_NAME)

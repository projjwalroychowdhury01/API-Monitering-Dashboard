import os
import sys

# Path to shared libraries (allows importing shared_logging even when running locally)
# Note: the shared_libraries folder lives at the repository root.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared_libraries/python")))

try:
    from shared_logging.logger import get_logger
except ImportError:
    # Fallback when shared library isn't available (e.g., local dev without PYTHONPATH)
    import logging

    def get_logger(service_name: str):
        return logging.getLogger(service_name)

from .config import settings

log = get_logger(settings.SERVICE_NAME)

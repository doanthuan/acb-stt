import logging
import os
from typing import Dict

from .config import settings


def get_logging_config() -> Dict:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] [%(module)s] %(levelname)s: %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
            "info_file_handler": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "default",
                "filename": os.path.join(settings.LOG_DIR, "server.log"),
                "maxBytes": settings.LOG_MAX_SIZE,
                "backupCount": settings.LOG_MAX_COUNTS,
            },
            "error_file_handler": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": logging.ERROR,
                "formatter": "default",
                "filename": os.path.join(settings.LOG_DIR, "server.log"),
                "maxBytes": settings.LOG_MAX_SIZE,
                "backupCount": settings.LOG_MAX_COUNTS,
            },
        },
        "root": {
            "level": settings.LOG_LEVEL,
            "handlers": ["console", "info_file_handler", "error_file_handler"],
        },
        "logger": {
            "output": {
                "level": settings.LOG_LEVEL,
            },
            "handlers": ["console", "info_file_handler", "error_file_handler"],
            "propagate": "no",
        },
    }

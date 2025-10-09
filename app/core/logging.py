import logging.config
import os
from datetime import datetime
from logging import getLogger

from app.core.config import settings

# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.path.dirname(__file__), '..', '.logs')
os.makedirs(logs_dir, exist_ok=True)

log_filename = f"tyriavault_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_filepath = os.path.join(logs_dir, log_filename)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "colored": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(asctime)s | %(message)s",
            "use_colors": True,
        },
        "file": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(asctime)s | %(message)s",
            "use_colors": False,
        },
    },
    "handlers": {
        "default": {
            "formatter": "colored",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "formatter": "file",
            "class": "logging.FileHandler",
            "filename": log_filepath,
            "mode": "w",
            "encoding": "utf-8",
        },
    },
    "root": {
        "handlers": ["file"],
        "level": settings.LOG_LEVEL,
    },
    "loggers": {
        "uvicorn": {
            "handlers": ["default", "file"],
            "level": settings.LOG_LEVEL,
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["file"],
            "level": settings.LOG_LEVEL,
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["file"],
            "level": settings.LOG_LEVEL,
            "propagate": False,
        },
    },
}
logging.config.dictConfig(LOGGING_CONFIG)
logger = getLogger("uvicorn")

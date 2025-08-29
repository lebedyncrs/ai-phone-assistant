import logging
from logging.handlers import TimedRotatingFileHandler

LOG_FILE = "logs/app.log"
LOG_ROTATION_WHEN = "midnight"
LOG_ROTATION_INTERVAL = 1
LOG_ROTATION_BACKUP_COUNT = 30
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.INFO

def configure_logging():
    """Configure logging with daily rotation"""
    file_handler = TimedRotatingFileHandler(
        filename=LOG_FILE,
        when=LOG_ROTATION_WHEN,
        interval=LOG_ROTATION_INTERVAL,
        backupCount=LOG_ROTATION_BACKUP_COUNT,
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    logging.basicConfig(level=LOG_LEVEL, handlers=[file_handler, logging.StreamHandler()])

    return logging.getLogger()

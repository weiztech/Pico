import os
from loguru import logger
from time import sleep

# LOG_FILE = os.environ.get("LOG_FILE")
log_format = "{time} - {name} - {level} - {message}"
# /var/log/project_name/LOG_FILE
# Change LOG_FILE in .env to enable or disable (empty) logging to a file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# if not LOG_FILE:
LOG_FILE = BASE_DIR + "/Log.log"
logger.add(
    LOG_FILE,
    format=log_format,
    serialize=True,
    level="DEBUG",
    rotation="1 week",
    compression="zip",
    colorize=True,
)

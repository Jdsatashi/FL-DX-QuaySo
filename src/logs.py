import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger()
logFormat = logging.Formatter("%(asctime)s - [%(levelname)s] - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormat)
logger.addHandler(consoleHandler)

fileHandler = RotatingFileHandler("logs/info.log", maxBytes=2048)
logger.addHandler(fileHandler)
fileHandler.setFormatter(logFormat)

# Create custom message log
message_logger = logging.getLogger('message_logger')
message_log_handler = logging.FileHandler('./logs/message.log')
message_log_formatter = logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s')
message_logger.setLevel(logging.INFO)
message_log_handler.setFormatter(message_log_formatter)
message_logger.addHandler(message_log_handler)
message_logger.info("This is a custom message log entry.")
message_logger.warning("This is another custom message log entry with a warning level.")

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from log_files.logs_path import log_folder_path

today = datetime.today().strftime("%d-%m-%Y")

msg_file = today + '_message.log'
app_log_file = today + '_info.log'

msg_path_file = os.path.join(log_folder_path, msg_file)
app_log_path_file = os.path.join(log_folder_path, app_log_file)

logger = logging.getLogger()
logFormat = logging.Formatter("%(asctime)s - [%(levelname)s] - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormat)
logger.setLevel(logging.DEBUG)
logger.addHandler(consoleHandler)

fileHandler = RotatingFileHandler(app_log_path_file, maxBytes=2048, encoding='utf-8')
logger.addHandler(fileHandler)
fileHandler.setFormatter(logFormat)

# Create custom message log
message_logger = logging.getLogger('message_logger')
message_log_handler = logging.FileHandler(msg_path_file, encoding='utf-8')
message_log_formatter = logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s')
message_logger.setLevel(logging.INFO)
message_log_handler.setFormatter(message_log_formatter)
message_logger.addHandler(message_log_handler)

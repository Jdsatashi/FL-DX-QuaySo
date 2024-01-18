import logging
import os
from datetime import datetime, time
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from log_files.logs_path import log_folder_path

today = datetime.today().strftime("%d-%m-%Y")

msg_file = 'message.log'
app_log_file = 'info.log'

msg_path_file = os.path.join(log_folder_path, msg_file)
app_log_path_file = os.path.join(log_folder_path, app_log_file)

backup_time1 = time(12, 0, 15)
backup_time2 = time(12, 0, 30)


# Terminal logger
logger = logging.getLogger()
logFormat = logging.Formatter("%(asctime)s - [%(levelname)s] - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormat)
logger.setLevel(logging.DEBUG)
logger.addHandler(consoleHandler)

fileHandler = TimedRotatingFileHandler(app_log_path_file, when="midnight", interval=30, backupCount=30)
logger.addHandler(fileHandler)
fileHandler.setFormatter(logFormat)


# Create custom message log
message_logger = logging.getLogger('message_logger')
message_log_handler = TimedRotatingFileHandler(msg_path_file, when="midnight", interval=30, backupCount=30)
message_log_formatter = logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s')
message_logger.setLevel(logging.INFO)
message_log_handler.setFormatter(message_log_formatter)
message_logger.addHandler(message_log_handler)

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from log_files.logs_path import log_folder_path


def create_log():
    today = datetime.today().strftime("%d-%m-%Y")

    msg_filename = today + '_message.log'
    app_log_filename = today + '_info.log'

    msg_path = os.path.join(log_folder_path, msg_filename)
    app_log_path = os.path.join(log_folder_path, app_log_filename)

    # Terminal logger
    new_logger = logging.getLogger()
    logFormat = logging.Formatter("%(asctime)s - [%(levelname)s] - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormat)
    new_logger.setLevel(logging.DEBUG)
    new_logger.addHandler(consoleHandler)

    fileHandler = RotatingFileHandler(app_log_path)
    new_logger.addHandler(fileHandler)
    fileHandler.setFormatter(logFormat)

    # Create custom message log
    msg_logger = logging.getLogger('message_logger')
    message_log_handler = RotatingFileHandler(msg_path)
    message_log_formatter = logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s')
    msg_logger.setLevel(logging.INFO)
    message_log_handler.setFormatter(message_log_formatter)
    msg_logger.addHandler(message_log_handler)
    return new_logger, msg_logger, msg_filename, app_log_filename, msg_path, app_log_path


logger, message_logger, msg_file, app_log_file, msg_path_file, app_log_path_file = create_log()

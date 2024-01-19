from datetime import datetime, timedelta

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os

from src import logs
from src.app import logger


def upload_to_drive(msg_filename, applog_filename, log_folder_path):
    # Authorize with Google
    gg_auth = GoogleAuth()
    drive = GoogleDrive(gg_auth)
    # Folder destination id
    folder = os.environ.get('GG_DRIVE_FOLDER')

    today = datetime.now().strftime('%d-%m-%Y')
    app_log = today + '_' + applog_filename.split('_')[1]
    msg_log = today + '_' + msg_filename.split('_')[1]
    app_log_path = log_folder_path + '/' + app_log
    msg_log_path = log_folder_path + '/' + msg_log
    # Handle create app log file and copy local content file
    file_app_log = drive.CreateFile({'parents': [{'id': folder}], 'title': app_log})
    file_app_log.SetContentFile(filename=app_log_path)
    logger.info(f"Uploading file log {app_log} to drive.")

    # Handle create message log file and copy local content file
    file_msg_log = drive.CreateFile({'parents': [{'id': folder}], 'title': msg_log})
    file_msg_log.SetContentFile(filename=msg_log_path)
    logger.info(f"Uploading file log {msg_log} to drive.")

    # Uploading to drive asd
    file_app_log.Upload()
    file_msg_log.Upload()

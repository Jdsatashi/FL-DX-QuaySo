from datetime import datetime, timedelta

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os

from src import logs


def upload_to_drive(file_send, filename):
    # Authorize with Google
    gg_auth = GoogleAuth()
    drive = GoogleDrive(gg_auth)

    # Folder destination id
    folder = os.environ.get('GG_DRIVE_FOLDER')

    today = datetime.now()
    app_log = filename['app_log_filename']
    msg_log = filename['msg_filename']
    app_log_path = file_send['app_log_path']
    msg_log_path = file_send['msg_log_path']
    # Handle create app log file and copy local content file
    file_app_log = drive.CreateFile({'parents': [{'id': folder}], 'title': app_log})
    file_app_log.SetContentFile(filename=app_log_path)
    logs.logger.info(f"Uploading file log {app_log} to drive.")

    # Handle create message log file and copy local content file
    file_msg_log = drive.CreateFile({'parents': [{'id': folder}], 'title': msg_log})
    file_msg_log.SetContentFile(filename=msg_log_path)
    logs.logger.info(f"Uploading file log {msg_log} to drive.")

    # Uploading to drive asd
    file_app_log.Upload()
    file_msg_log.Upload()

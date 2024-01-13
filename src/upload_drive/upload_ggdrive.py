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

    # Handle create app log file and copy local content file
    file_app_log = drive.CreateFile({'parents': [{'id': folder}], 'title': filename['app_log_filename']})
    file_app_log.SetContentFile(filename=file_send['app_log_path'])
    logs.logger.info(f"Uploading file log {filename['app_log_filename']} to drive.")

    # Handle create message log file and copy local content file
    file_msg_log = drive.CreateFile({'parents': [{'id': folder}], 'title': filename['msg_filename']})
    file_msg_log.SetContentFile(filename=file_send['msg_log_path'])
    logs.logger.info(f"Uploading file log {filename['app_log_filename']} to drive.")

    # Uploading to drive
    file_app_log.Upload()
    file_msg_log.Upload()

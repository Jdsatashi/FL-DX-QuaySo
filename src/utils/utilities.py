from _datetime import datetime

from src import logs
from src.mongodb import ROLE_TABLE

import os

# Get user role id
role = ROLE_TABLE.find_one({'role': 'auth_user'})
role_auth_id = str(role['_id']) if role else ROLE_TABLE.find_one(
    {'role': 'auth_user'})

# Get admin role id
role_admin = ROLE_TABLE.find_one({'role': 'admin'})
role_admin_id = str(role_admin['_id']) if role_admin else ROLE_TABLE.find_one(
    {'role': 'admin'})


# Create new folder and get path
def create_folder(folder_name):
    year = datetime.utcnow().year
    uploads_event_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
    year_path = os.path.join(uploads_event_folder, str(year))
    folder_path = os.path.join(year_path, folder_name)
    logs.logger.info(f"Make folder {folder_path}")
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return folder_path

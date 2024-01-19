import os

from dotenv import load_dotenv

load_dotenv()


# Flask run environment
FLASK_PORT = os.environ.get('FLASK_RUN_PORT')
FLASK_HOST = os.environ.get('FLASK_RUN_HOST')
FLASK_DEBUG = os.environ.get('FLASK_DEBUG')

# Flask App environment
SECRET_KEY = os.environ.get('SECRET_KEY')

# Mongodb environment
MONGO_URI = os.environ.get('MONGO_URI')
DB_NAME = os.environ.get('DB_NAME')

# Google Drive folder
FOLDER_ID = os.environ.get('GG_DRIVE_FOLDER')

# Admin account
ADMIN_USER = os.environ.get('ADMIN_USER')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

from flask import Flask
import os
from dotenv import load_dotenv
from _datetime import datetime

# Loading environment variables
load_dotenv()

# Create logs folder
if not os.path.exists("logs"):
    os.makedirs("logs")

# Add custom logging
from src import logs

# Create app
app = Flask(__name__)

# Create database mongodb and tables/collections
from src import mongodb

# Create absolutely paths to local storage
uploads_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'src', 'static', 'uploads')


def create_folder(event_name):
    year = datetime.utcnow().year
    uploads_event_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
    year_path = os.path.join(uploads_event_folder, str(year))
    folder_path = os.path.join(year_path, event_name)
    print(f"Make folder {folder_path}")
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return folder_path


# Add configuration for Flask
app.config.from_mapping(
    SECRET_KEY=os.environ.get('SECRET_KEY'),
    UPLOAD_FOLDER=uploads_folder
)

# Add default role and create admin account
from src.requests.role import add_default_role, create_admin_account

add_default_role()
create_admin_account()

# Add all routes
from src import routes

# Register prefix url
app.register_blueprint(routes.auth_route.auth, url_prefix='/auth')
app.register_blueprint(routes.admin_route.admin, url_prefix='/admin')
app.register_blueprint(routes.event.events, url_prefix='/events')

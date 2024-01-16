from flask import Flask
from dotenv import load_dotenv
from _datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

import os

# Loading environment variables
load_dotenv()

# Add schedular
scheduler = BackgroundScheduler()

# Create log_files folder
if not os.path.exists("log_files"):
    os.makedirs("log_files")

# Add custom logging
from src import logs

# Create app
app = Flask(__name__)

# Create database mongodb and tables/collections
from src import mongodb

# Create absolutely paths to local storage
uploads_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'src', 'static', 'uploads')

# Add configuration for Flask
app.config.from_mapping(
    SECRET_KEY=os.environ.get('SECRET_KEY'),
    UPLOAD_FOLDER=uploads_folder
)

# Add default role and create admin account
from src.requests.role import add_default_role, create_admin_account

with app.app_context():
    add_default_role()
    create_admin_account()

# Add all routes
from src import routes

# Register prefix url
app.register_blueprint(routes.auth_route.auth, url_prefix='/user')
app.register_blueprint(routes.admin_route.admin, url_prefix='/admin')
app.register_blueprint(routes.event.events, url_prefix='/events')

from src.models import Models
from src.mongodb import EVENT_TABLE, ACCOUNT_TABLE
from src.utils.utilities import update_user_join, auto_random, update_user_role
from src.upload_drive import upload_ggdrive


# Upload daily log_files
def upload_daily_log():
    logs.logger.info("Upload daily log files to drive.")
    upload_ggdrive.upload_to_drive(
        {'msg_log_path': logs.msg_path_file, 'app_log_path': logs.app_log_path_file},
        {'msg_filename': logs.msg_file, 'app_log_filename': logs.app_log_file, 'file_path': logs.log_folder_path}
        )
    logs.logger.info("End process upload logs to drive.")


# Daily jobs function asd
def check_active():
    # Assign event and user model
    event_model = Models(table=EVENT_TABLE)
    user_model = Models(table=ACCOUNT_TABLE)
    # Get all events and all users
    events = event_model.get_all()
    users = user_model.get_all()
    # Update user who has no role
    for user in users:
        update_user_role(str(user['_id']))
    # Get current time
    now = datetime.now()
    # Format date time to year-month-date
    current_date = now.strftime('%Y-%m-%d')
    for event in events:
        # Get date close for comparing
        close_date = event['date_close']
        # Format to close date to datetime data type
        close_datetime = datetime.strptime(close_date, '%Y-%m-%d')
        # Get 3 dates before date close
        last_3_date = close_datetime - timedelta(days=3)
        # Change active status for event
        is_active = False if current_date > close_date else True
        event_model.update(event['_id'], {'is_active': is_active})
        logs.message_logger.info(f"Update '{event['event_name']}' daily.")
        # Check and update all users numbers selected
        update_user_join(str(event['_id']))

        logs.message_logger.info(f"Event id: {str(event['_id'])}")
        # Handle auto selected numbers for user
        if close_date >= current_date > last_3_date.strftime('%Y-%m-%d'):
            logs.message_logger.info(f"Auto random event '{event['event_name']}' in the last 3 days.")
            auto_random(str(event['_id']))
            auto_random(str(event['_id']))
    # Refresh new logs for everyday
    logs.create_log()
    logs.logger.info(f"New logs file.")
    logs.message_logger.info(f"New message logs file.")


# Date time to proceed daily jobs test
scheduler.add_job(
    func=check_active,
    trigger="cron",
    hour="0",
    minute="0",
    second="25",
    timezone="Asia/Ho_Chi_Minh",
)

# Upload log files daily
scheduler.add_job(
    func=upload_daily_log,
    trigger="cron",
    hour="23",
    minute="59",
    timezone="Asia/Ho_Chi_Minh",
)

# Run scheduler
scheduler.start()

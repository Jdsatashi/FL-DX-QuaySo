from flask import Flask
from dotenv import load_dotenv
from _datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

import os

from src.utils.constants import DATE_RANDOM, RAMDOM_HOUR, RANDOM_MINUTE
from src.utils.env import SECRET_KEY

# Loading environment variables
load_dotenv()

# Create database mongodb and tables/collections
from src import mongodb

# Add schedular
scheduler = BackgroundScheduler()

# Create log_files folder
if not os.path.exists("log_files"):
    os.makedirs("log_files")

# Add custom logging
from src import logs
logger, message_logger, msg_file, app_log_file, log_date = logs.create_log()

# Create app
app = Flask(__name__)

# Create absolutely paths to local storage
uploads_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'src', 'static', 'uploads')

# Add configuration for Flask
app.config.from_mapping(
    SECRET_KEY=SECRET_KEY,
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


# Upload daily log_files | Fix error
def upload_daily_log():
    upload_ggdrive.upload_to_drive(
        msg_file, app_log_file, logs.log_folder_path
        )
    logger.info("End process upload logs to drive.")


# Daily jobs function
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
        # Change active status for event
        is_active = False if current_date > close_date else True
        event_model.update(event['_id'], {'is_active': is_active})
        message_logger.info(f"Update '{event['event_name']}' daily.")
        # Check and update all users numbers selected
        update_user_join(str(event['_id']))
        message_logger.info(f"Event id: {str(event['_id'])}")
    # Refresh new logs for everyday
    today = now.strftime('%d-%m-%Y')
    if today > log_date:
        # clear old logs
        logs.clear_log_handlers(logger)
        logs.clear_log_handlers(message_logger)
        logger.info(f"Clear old logs file.")
        # Create new logs
        logs.create_log()
        logger.info(f"New logs file.")
        message_logger.info(f"New message logs file.")


def random_schedular():
    # Get all event
    events = list(EVENT_TABLE.find())
    # Get current date
    now = datetime.now()
    current_date = now.strftime('%Y-%m-%d')
    # If events have multi event
    if len(events) > 1:
        for event in events:
            check_for_random(event, current_date)
    # If events have 1 event
    elif len(events) == 1:
        check_for_random(events[0], current_date)
    else:
        logger.error("Error when get 'events' for auto random")


def check_for_random(event, current_date):
    # Get date close for comparing
    close_date = event['date_close']
    # Format to close date to datetime data type
    close_datetime = datetime.strptime(close_date, '%Y-%m-%d')
    # Get dates before date close
    last_random_date = close_datetime - timedelta(days=DATE_RANDOM)
    # Handle auto selected numbers for user
    if current_date == last_random_date.strftime('%Y-%m-%d'):
        # Check event
        message_logger.info(f"Checking event: {event['event_name']}")
        update_user_join(str(event['_id']))
        message_logger.info(f"Auto random event '{event['event_name']}' in the last this days.")
        auto_random(str(event['_id']))
        auto_random(str(event['_id']))


# Date time to proceed daily jobs test
scheduler.add_job(
    func=check_active,
    trigger="cron",
    hour="0",
    minute="0",
    second="15",
    timezone="Asia/Ho_Chi_Minh",
)

# Process auto random
scheduler.add_job(
    func=random_schedular,
    trigger="cron",
    hour=str(RAMDOM_HOUR),
    minute=str(RANDOM_MINUTE),
    second="00",
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

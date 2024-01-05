from flask import Flask
from dotenv import load_dotenv
from _datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

import os


# Loading environment variables
load_dotenv()

# os.add_dll_directory(r"C:\Program Files\GTK3-Runtime Win64\bin")

scheduler = BackgroundScheduler()

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
from src.mongodb import EVENT_TABLE
from src.utils.utilities import update_user_join, auto_random


# Daily jobs function
def check_active():
    event_model = Models(table=EVENT_TABLE)
    events = event_model.get_all()
    now = datetime.now()
    current_date = now.strftime('%Y-%m-%d')
    last_3_date = now - timedelta(days=3)
    for event in events:
        form_date = event['date_close']
        is_active = False if current_date > form_date else True
        event_model.update(event['_id'], {'is_active': is_active})
        logs.message_logger.info(f"Update {event['event_name']} daily.")
        update_user_join(str(event['_id']))
        if current_date > event['date_close'] > last_3_date.strftime('%Y-%m-%d'):
            logs.message_logger.info(f"Auto random in the last 3 days.")
            auto_random(str(event['_id']))


# Date time to proceed daily jobs
scheduler.add_job(
    func=check_active,
    trigger="cron",
    hour="16",
    minute="6",
    timezone="Asia/Ho_Chi_Minh",
)

# Run scheduler
scheduler.start()

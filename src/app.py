from flask import Flask
import os
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt

load_dotenv()

from src import logs

app = Flask(__name__)
# csrf = CSRFProtect(app)

from src import mongodb

app.config.from_mapping(
    SECRET_KEY=os.environ.get('SECRET_KEY'),
)
#
bcrypt = Bcrypt(app)

from src.requests.role import add_default_role, create_admin_account

add_default_role()
create_admin_account()
# Add all routes
from src import routes

# Register prefix
app.register_blueprint(routes.auth_route.auth, url_prefix='/auth')
app.register_blueprint(routes.admin_route.admin, url_prefix='/admin')
app.register_blueprint(routes.event.events, url_prefix='/events')

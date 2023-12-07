from flask import Blueprint

from src.mongodb import EVENT_TABLE, USER_JOIN_EVENT as join_in


events = Blueprint('event', __name__)


@events.route('/')
def index():
    return "Hello, World!"

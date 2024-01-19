from pymongo import MongoClient
from dotenv import load_dotenv
from src.utils.env import MONGO_URI, DB_NAME

load_dotenv()

# Add mongo uri to python mongo client
mongo_client = MongoClient(MONGO_URI)

# Get Mongo database
mongodb = mongo_client.get_database(DB_NAME)
ACCOUNT_TABLE = mongodb.get_collection('account')
ROLE_TABLE = mongodb.get_collection('role')
ROLL_TABLE = mongodb.get_collection('roll_number_selected')
EVENT_TABLE = mongodb.get_collection('event')
USER_JOIN_EVENT = mongodb.get_collection('user_join_event')

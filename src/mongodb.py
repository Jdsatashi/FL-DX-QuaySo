from pymongo import MongoClient
import os

# Add mongo uri to python mongo client
mongo_uri = os.environ.get('MONGO_URI')
mongo_client = MongoClient(mongo_uri)

# Get Mongo database
db_name = os.environ.get('DB_NAME')
mongodb = mongo_client.get_database(db_name)
ACCOUNT_TABLE = mongodb.get_collection('account')
ROLE_TABLE = mongodb.get_collection('role')
ROLL_TABLE = mongodb.get_collection('roll_number_selected')

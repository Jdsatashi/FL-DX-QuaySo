from _datetime import datetime
import bcrypt
from bson import ObjectId

from src.mongodb import ROLE_TABLE, ACCOUNT_TABLE
from src.utils.utilities import role_admin_id


def add_default_role():
    roles = [
        {"role": "admin"},
        {"role": "manager"},
        {"role": "auth_user"},
    ]
    for role in roles:
        if not ROLE_TABLE.find_one(role):
            ROLE_TABLE.insert_one(role)


def create_admin_account():
    admin = ACCOUNT_TABLE.find_one({'username': 'admin'})
    if not admin:
        password = 'dxAdministrator'.encode("utf-8")
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
        ACCOUNT_TABLE.insert_one({
            "username": 'admin',
            "email": 'vdt1073@gmail.com',
            "password": hashed_password,
            "role_id": role_admin_id,
            "date_created": datetime.utcnow()
        })

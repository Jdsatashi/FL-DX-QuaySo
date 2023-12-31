from _datetime import datetime
import bcrypt

from src.mongodb import ROLE_TABLE, ACCOUNT_TABLE
from src.utils.utilities import role_admin_id as is_admin
from src.logs import message_logger, logger


def add_default_role():
    roles = [
        {"role": "admin"},
        {"role": "auth_user"},
    ]
    for role in roles:
        if not ROLE_TABLE.find_one(role):
            message_logger.info(f"Adding default role: {role['role']}")
            ROLE_TABLE.insert_one(role)


def create_admin_account():
    admin = ACCOUNT_TABLE.find_one({'username': 'ADMIN'})
    if not admin:
        role_admin_id = is_admin
        logger.info(f"is_admin: {is_admin}")
        if is_admin is None:
            add_default_role()
            role_admin = ROLE_TABLE.find_one({'role': 'admin'})
            role_admin_id = str(role_admin['_id']) if role_admin else ROLE_TABLE.find_one(
                {'role': 'admin'})
        password = 'dxAdministrator'.encode("utf-8")
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
        try:
            ACCOUNT_TABLE.insert_one({
                "username": 'ADMIN',
                "password": hashed_password,
                "role_id": role_admin_id,
                "date_created": datetime.utcnow()
            })
            message_logger.info("Added admin account.")
        except Exception as e:
            logger.error("Create admin errors. ", e)

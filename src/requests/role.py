import os
import traceback
from _datetime import datetime
import bcrypt

from src.mongodb import ROLE_TABLE, ACCOUNT_TABLE
from src.utils.utilities import role_admin_id as is_admin
from src.app import message_logger, logger


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
    admin_username = os.environ.get('ADMIN_USER')
    admin = ACCOUNT_TABLE.find_one({'username': admin_username})
    if not admin:
        role_admin_id = is_admin
        logger.info(f"is_admin: {is_admin}")
        if is_admin is None:
            add_default_role()
            role_admin = ROLE_TABLE.find_one({'role': 'admin'})
            role_admin_id = str(role_admin['_id']) if role_admin else ROLE_TABLE.find_one(
                {'role': 'admin'})
        try:
            admin_password = os.environ.get('ADMIN_PASSWORD')
            hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
            ACCOUNT_TABLE.insert_one({
                "username": admin_username,
                "password": hashed_password,
                "role_id": role_admin_id,
                "date_created": datetime.utcnow()
            })
            message_logger.info("Added admin account.")
        except Exception as e:
            error = traceback.format_exc()
            logger.error("Create admin errors. ", f"Error type: {e}", f"\n{error}")

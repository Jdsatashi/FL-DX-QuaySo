from flask import flash, redirect, url_for
import validators

from src.logs import message_logger, fileHandler
from src.mongodb import ROLE_TABLE, ACCOUNT_TABLE

role = ROLE_TABLE.find_one({'role': 'auth_user'})
role_auth_id = str(role['_id']) if role else ROLE_TABLE.find_one(
    {'role': 'auth_user'})

role_admin = ROLE_TABLE.find_one({'role': 'admin'})
role_admin_id = str(role_admin['_id']) if role_admin else ROLE_TABLE.find_one(
    {'role': 'admin'})


def validate_account_create(emails, username):
    if not validators.email(emails):
        flash(f"Email was not valid.", "warning")
        return redirect(url_for('admin.account_create'))
    if ACCOUNT_TABLE.find_one(username):
        flash(f"Username of Email.", "warning")
        return redirect(url_for('admin.account_create'))
    if ACCOUNT_TABLE.find_one(emails):
        flash(f"Email {emails} was used.", "warning")
        return redirect(url_for('admin.account_create'))


# def log_info(message):
#     message_logger.info(message)
#
#
# def log_debug(message):
#     fileHandler.debug(message)

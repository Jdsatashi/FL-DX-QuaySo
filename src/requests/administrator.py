from _datetime import datetime
from bson import ObjectId
from flask import render_template, redirect, request, flash, url_for, Blueprint

from src.logs import message_logger, logger
from src.requests.authenticate import admin_authorize
from src.forms import CreateAccountForm, UpdateAccountForm
from src.models import Models
from src.mongodb import ACCOUNT_TABLE, USER_JOIN_EVENT
from src.utils.utilities import role_auth_id, create_folder
from src.requests.event import event_model, join_event_model

import os
import bcrypt
import traceback
import pandas as pd


admin = Blueprint('admin', __name__)
# Assign account as account table model
account = Models(table=ACCOUNT_TABLE)


# Get all accounts
@admin.route('/accounts/')
def account_manager():
    # Authorize is admin
    adm = admin_authorize()
    if not adm:
        flash("Bạn không được phép truy cập vào trang này.", 'danger')
        return redirect(url_for('home'))
    # Get all accounts data exclude admin accounts
    account_data = list(account.get_all_exclude({'_id': {'$ne': ObjectId(adm['_id'])}}))
    try:
        # Edit some sensitive data in account data
        for data in account_data:
            # Remove password
            data.pop('password')
            # Change ObjectId to String
            data['_id'] = str(data['_id'])
            data['role_id'] = str(data['role_id'])
            # Add is_active if account does not have it
            if 'is_active' not in data:
                account.update(ObjectId(data['_id']), {'is_active': True})
                data['is_active'] = True
        logger.info("Get all data account success.")
        return render_template('admin/account/index.html', accounts=account_data, title="Quản l tài khoản")
    # Return error
    except Exception as e:
        error_info = traceback.format_exc()
        logger.error(f'Error when direct to manage account page.\nError: {e}\n{error_info}"')
        flash('Server gặp sự cố, vui lòng thử lại sau.', 'warning')
        return redirect(url_for('home'))


@admin.route('/accounts/create', methods=['GET', 'POST'])
def account_create():
    # Authorize is admin
    adm = admin_authorize()
    if not adm:
        flash("Bạn không được phép truy cập vào trang này.", 'danger')
        return redirect(url_for('home'))
    # Get Form data
    form = CreateAccountForm()
    # Get all events existing
    events = list(event_model.get_all())
    # Handle create method is POST
    if request.method == 'POST':
        # Encrypt password
        password = form.password.data.encode("utf-8")
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
        # Data dict for input
        form_user = {
            "username": str(form.username.data).upper(),
            "usercode": form.usercode.data.upper(),
            "password": hashed_password,
            "role_id": role_auth_id,
            "is_active": True,
            "date_created": datetime.utcnow()
        }
        # Event to assign
        events_join = form.join_event.data
        # Validate if username is existing
        if ACCOUNT_TABLE.find_one(form_user['username']):
            flash(f"Username đã tồn tại.", "warning")
            return redirect(url_for('admin.account_create'))
        # Validate Form
        if form.validate_on_submit():
            try:
                # Create account
                account.create(form_user)
                # Assign user to event when events_join exist
                if events_join != '':
                    # Split event _id if joining multi event
                    events_join = events_join.split('|')
                    # Edit data out put
                    form_user.update({'events': {}})
                    form_user.pop('password')
                    form_user.pop('role_id')
                    for event in events_join:
                        event = event.split(',')
                        # Get event _id and point_exchange
                        event_data = event_model.get_one({'_id': ObjectId(event[0])})
                        # Calculate turn_roll
                        turn_roll = int(event[1]) // int(event_data['point_exchange'])
                        # Data to insert into user join event
                        input_data = {
                            'user_id': str(form_user['_id']),
                            'event_id': event[0],
                            'user_point': int(event[1]),
                            'turn_roll': turn_roll
                        }
                        form_user['events'].update({event[0]: input_data})
                        # # Handle insert user join event to database
                        join_event_model.create(input_data)
                # Return when successful
                message_logger.info(f"Created successfully {form_user}.")
                flash(f"Tạo thành công tài khoản '{form_user['username']}'.", "success")
                return redirect(url_for('admin.account_manager'))
            # Return error
            except Exception as e:
                error_info = traceback.format_exc()
                logger.error(f'Error when create user.\nError: {e}\n{error_info}"')
                flash('Server gặp sự cố, vui lòng thử lại sau.', 'warning')
                return redirect(url_for('admin.account_manager'))
        flash('Một vài trường thông tin bị sai, vui lòng thử lại.', 'warning')
        return redirect(url_for('admin.account_manager'))
    # Render form data when method is GET
    else:
        return render_template('admin/account/create.html', title='Create account', form=form, events=events)


# Create list accounts
@admin.route('accounts/list/add', methods=['POST', 'GET'])
def account_add_list():
    # Authorize is admin
    adm = admin_authorize()
    if not adm:
        flash("Bạn không được phép truy cập vào trang này.", 'danger')
        return redirect(url_for('home'))
    if request.method == 'POST':
        # Get file
        uploaded_file = request.files['csv_list']
        # Secure filename
        file_name = uploaded_file.filename
        if file_name != '':
            try:
                # Create folder and get path
                folder_path = create_folder("csv")
                name, ext = os.path.splitext(file_name)
                # Validate filename and rename
                new_filename = check_file_name(folder_path, uploaded_file)
                # Get file path
                file_path = os.path.join(folder_path, new_filename)
                # Try save file
                try:
                    uploaded_file.save(file_path)
                except Exception as e:
                    error_info = traceback.format_exc()
                    logger.error(f'Error save file.\nError: {e}\n{error_info}"')
                # Column name
                col_name = ['usercode', 'username', 'point_dm2', 'address', 'event']
                # Check extension match with pandas reader type
                match ext:
                    case '.xlsx':
                        csv_data = pd.read_excel(file_path, names=col_name, header=None)
                    case '.csv':
                        csv_data = pd.read_csv(file_path, names=col_name, header=None)
                    case _:
                        flash(f"Định dạng file phải là '.csv' hoặc '.xlsx'.", "warning")
                        return redirect(url_for('admin.account_add_list'))
                # Get event name from event column at first row
                event_name = csv_data.loc[0, 'event']
                # Get event data from event name
                event = event_model.get_one({'event_name': event_name})
                event_id = str(event['_id'])
                # Get current date time for create or update
                now = datetime.utcnow()
                # Loop through data in csv file
                for i, row in csv_data.iterrows():
                    if int(i) > 0:
                        # Hashing password
                        hashed_password = bcrypt.hashpw(row['username'].lower().encode("utf-8"), bcrypt.gensalt())
                        # Add data to data dict
                        data_dict = {
                            'username': row['username'].upper(),
                            'usercode': row['usercode'].upper(),
                            'password': hashed_password,
                            'address': row['address'],
                        }
                        is_existed = account.get_one({'username': data_dict['username']})
                        # Try adding of update account
                        try:
                            # When account not exited creating new account
                            if is_existed is None:
                                data_dict.update({'date_created': now})
                                account.create(data_dict)
                            # When account exited updating account
                            else:
                                data_dict.update({'date_updated': now})
                                account.update(is_existed['_id'], data_dict)
                        # Except error
                        except Exception as e:
                            error_info = traceback.format_exc()
                            logger.error(f'Error when adding user {data_dict["username"]}.\nError: {e}\n{error_info}"')
                            flash(f"Error when add file {uploaded_file.filename}!", 'warning')
                            return redirect(url_for('admin.account_add_list'))
                flash(f"Added file: {uploaded_file.filename} successfully!", 'success')
                return redirect(url_for('admin.account_add_list'))
            except Exception as e:
                error_info = traceback.format_exc()
                logger.error(f'Error when upload csv list.\nError: {e}\n{error_info}"')
                flash(f"Error when add file {uploaded_file.filename}!", 'warning')
                return redirect(url_for('admin.account_add_list'))
    return render_template('admin/account/input_csv.html')


# Updating accounts
@admin.route('account/<string:_id>', methods=['POST', 'GET'])
def account_edit(_id):
    # Authorize is admin
    adm = admin_authorize()
    if not adm:
        flash("Bạn không được phép truy cập vào trang này.", 'danger')
        return redirect(url_for('home'))
    # Get data were created
    events = list(event_model.get_all())
    user_joins = list(join_event_model.get_many({'user_id': _id}))
    event_not_join = list()
    event_join = dict()
    # Create event_join dict to store require data to showing
    for event in user_joins:
        event_join.update({event['event_id']: {}})
    # Add event data to event_join dict
    for event in events:
        event['_id'] = str(event['_id'])
        if event['_id'] not in event_join:
            event_not_join.append(event)
        else:
            event_join.pop(event['_id'])
            event_join.update({event['_id']: {'event_name': event['event_name']}})
    # Add turn roll of user joined events to event_join dict
    for event in user_joins:
        if event['event_id'] in event_join:
            event_join[event['event_id']].update({'turn_roll': event['turn_roll'], 'user_point': event['user_point']})
    # Get form data
    form = UpdateAccountForm()
    # Get user data for updating
    user = account.get_one({'_id': ObjectId(_id)})
    if not user:
        flash('Không tìm thấy tài khoản.', 'warning')
        return redirect(url_for('home'))
    # Update user method
    if request.method == 'POST':
        # Get data from Form
        events_join = form.join_event.data
        form_data = {
            "username": str(form.username.data).upper(),
            "usercode": form.usercode.data.upper(),
            "is_active": form.is_active.data,
            "date_updated": datetime.utcnow()
        }
        # Validate Form
        if form.validate_on_submit():
            # Add fields date update to user
            if 'date_updated' not in user:
                account.update(ObjectId(_id), {'date_updated': ''})
            # Handle updating user account
            try:
                # Updating account
                edit_account = account.update(ObjectId(_id), form_data)
                # Get user point for calculating turns roll
                form_data.update({'events': {}})
                # Assign event for user when events_join (string from Form) is not ''
                if events_join != '':
                    events_join = events_join.split('|')
                    for event in events_join:
                        event = event.split(',')
                        # Get event point_exchange to calculate turn roll
                        event_data = event_model.get_one({'_id': ObjectId(event[0])})
                        turn_roll = int(event[1]) // int(event_data['point_exchange'])
                        # Data to insert into database
                        input_data = {
                            'user_id': _id,
                            'event_id': event[0],
                            'user_point': int(event[1]),
                            'turn_roll': turn_roll
                        }
                        form_data['events'].update({event[0]: input_data})
                        # Check if user has already joined event
                        has_exists = join_event_model.get_one({'event_id': event[0], 'user_id': _id})
                        # Created when user not joined yet
                        if has_exists is None:
                            join_event_model.create(input_data)
                        # Updated when user joined
                        else:
                            join_event_model.update(has_exists['_id'], input_data)
                        # Remove event_id from original event joining
                        if event[0] in event_join:
                            event_join.pop(event[0])
                # Delete event joined when user was removed from event
                for event in event_join:
                    # Get _id of user_join_event table
                    data_delete = join_event_model.get_one({'user_id': _id, 'event_id': event})
                    # Handle deleting
                    USER_JOIN_EVENT.delete_one({'_id': data_delete['_id']})
                # Done jobs, return success
                message_logger.info(f"Admin cập nhật tài khoản {user['username']}.\nNội dung: {form_data}")
                flash(f'Cập nhật tài khoản "{edit_account["username"]}".', 'success')
                return redirect(url_for('admin.account_manager'))
            # Return Errors
            except Exception as e:
                error_info = traceback.format_exc()
                logger.error(f'Error when editing account.\nError: {e}\n{error_info}"')
                flash('Server gặp sự cố, vui lòng thử lại sau.', 'warning')
                return redirect(url_for('admin.account_manager'))
        flash('Một số thông tin bị lỗi, vui lòng kiểm tra lại.', 'warning')
        return redirect(url_for('admin.account_edit', _id=_id))
    logger.info("Admin edit account!")
    # Render template for GET methods
    return render_template(
        'admin/account/edit.html',
        form=form, account=user,
        _id=user['_id'],
        events=event_not_join,
        event_join=event_join
    )


# Rename file if file exist in same path
def check_file_name(path, file):
    file_name = file.filename
    base, ext = os.path.splitext(file_name)
    num = 1
    while os.path.isfile(os.path.join(path, file_name)):
        file_name = f"{base}-({num}){ext}"
        num += 1
    return file_name

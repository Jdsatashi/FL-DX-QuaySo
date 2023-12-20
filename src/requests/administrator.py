from _datetime import datetime
from bson import ObjectId
from flask import render_template, redirect, request, flash, url_for, Blueprint

from src.logs import message_logger, logger
from src.requests.authenticate import admin_authorize
from src.forms import CreateAccountForm, UpdateAccountForm
from src.models import Models
from src.mongodb import ACCOUNT_TABLE, USER_JOIN_EVENT
from src.utils.utilities import role_auth_id
from src.requests.event import event_model, join_event_model

import bcrypt

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
        return render_template('admin/account/index.html', accounts=account_data)
    # Return error
    except Exception as e:
        print(f"Error.\n{e}")
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
            "username": str(form.username.data).lower(),
            "usercode": form.usercode.data,
            "point": form.point.data,
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
                        # Get event _id and point_exchange
                        event_data = event_model.get_one({'_id': ObjectId(event)})
                        # Calculate turn_roll
                        turn_roll = form_user['point'] // int(event_data['point_exchange'])
                        # Data to insert into user join event
                        input_data = {
                            'user_id': str(form_user['_id']),
                            'event_id': event,
                            'turn_roll': turn_roll
                        }
                        form_user['events'].update({event: input_data})
                        # Handle insert to database
                        join_event_model.create(input_data)
                # Return when successful
                message_logger.info(f"Created successfully {form_user}.")
                flash(f"Tạo thành công tài khoản '{form_user['username']}'.", "success")
                return redirect(url_for('admin.account_manager'))
            # Return error
            except Exception as e:
                logger.error(f"Error when create user.\n{e}")
                flash('Server gặp sự cố, vui lòng thử lại sau.', 'warning')
                return redirect(url_for('admin.account_manager'))
    # Render form data when method is GET
    else:
        return render_template('admin/account/create.html', title='Create account', form=form, events=events)


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
            event_join[event['event_id']].update({'turn_roll': event['turn_roll']})
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
            "username": str(form.username.data).lower(),
            "usercode": form.usercode.data,
            "point": form.point.data,
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
                user['point'] = int(user['point'])
                form_data.update({'events': {}})
                # Assign event for user when events_join (string from Form) is not ''
                if events_join != '':
                    events_join = events_join.split('|')
                    for event in events_join:
                        # Get event point_exchange to calculate turn roll
                        event_data = event_model.get_one({'_id': ObjectId(event)})
                        turn_roll = int(form.point.data) // int(event_data['point_exchange'])
                        # Data to insert into database
                        input_data = {
                            'user_id': _id,
                            'event_id': event,
                            'turn_roll': turn_roll
                        }
                        form_data['events'].update({event: input_data})
                        # Check if user has already joined event
                        has_exists = join_event_model.get_one({'event_id': event, 'user_id': _id})
                        # Created when user not joined yet
                        if has_exists is None:
                            join_event_model.create(input_data)
                        # Updated when user joined
                        else:
                            join_event_model.update(has_exists['_id'], input_data)
                        # Remove event_id from original event joining
                        if event in event_join:
                            event_join.pop(event)
                # Delete event joined when user was removed from event
                for event in event_join:
                    # Get _id of user_join_event table
                    data_delete = join_event_model.get_one({'user_id': _id, 'event_id': event})
                    # Handle deleting
                    USER_JOIN_EVENT.delete_one({'_id': data_delete['_id']})
                # Return success
                message_logger.info(f"Admin cập nhật tài khoản {user['username']}.\nNội dung: {form_data}")
                flash(f'Cập nhật tài khoản "{edit_account["username"]}".', 'success')
                return redirect(url_for('admin.account_manager'))
            # Return Errors
            except Exception as e:
                logger.error('Error when editing account.', e)
                flash('Server gặp sự cố, vui lòng thử lại sau.', 'warning')
                return redirect(url_for('admin.account_manager'))
        flash('Một số thông tin bị lỗi, vui lòng kiểm tra lại.', 'warning')
        return redirect(url_for('admin.account_edit'))
    logger.info("Admin edit account!")
    # Render template for GET methods
    return render_template(
        'admin/account/edit.html',
        form=form, account=user,
        _id=user['_id'],
        events=event_not_join,
        event_join=event_join
    )

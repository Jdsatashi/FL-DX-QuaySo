from _datetime import datetime
from bson import ObjectId
from flask import render_template, redirect, request, flash, url_for, Blueprint
from src.requests.authenticate import admin_authorize
from src.forms import CreateAccountForm, UpdateAccountForm
from src.models import Models
from src.mongodb import ACCOUNT_TABLE
from src.utils.utilities import role_auth_id
from src.requests.event import event_model, join_event_model

import bcrypt

admin = Blueprint('admin', __name__)
account = Models(table=ACCOUNT_TABLE)


@admin.route('/accounts/')
def account_manager():
    adm = admin_authorize()
    if not adm:
        flash("Bạn không được phép truy cập vào trang này.", 'danger')
        return redirect(url_for('home'))
    account_data = account.get_all()
    try:
        data_list = list(account_data)
        for data in data_list:
            data.pop('password')
            data['_id'] = str(data['_id'])
            data['role_id'] = str(data['role_id'])
            if 'turn_roll' not in data:
                account.update(ObjectId(data['_id']), {'turn_roll': 0})
                data['turn_roll'] = 0
            if 'is_active' not in data:
                account.update(ObjectId(data['_id']), {'is_active': True})
                data['is_active'] = True
        return render_template('admin/account/index.html', accounts=data_list)
    except Exception as e:
        print(f"Error.\n{e}")
        flash('Server gặp sự cố, vui lòng thử lại sau.', 'warning')
        return redirect(url_for('home'))


@admin.route('/accounts/create', methods=['GET', 'POST'])
def account_create():
    adm = admin_authorize()
    if not adm:
        flash("Bạn không được phép truy cập vào trang này.", 'danger')
        return redirect(url_for('home'))
    form = CreateAccountForm()
    events = list(event_model.get_all())
    if request.method == 'POST':
        password = form.password.data.encode("utf-8")
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

        form_user = {
            "username": str(form.username.data).lower(),
            "usercode": form.usercode.data,
            "point": form.point.data,
            "password": hashed_password,
            "role_id": role_auth_id,
            "is_active": True,
            "date_created": datetime.utcnow()
        }
        events_join = form.join_event.data

        if ACCOUNT_TABLE.find_one(form_user['username']):
            flash(f"Username đã tồn tại.", "warning")
            return redirect(url_for('admin.account_create'))

        if form.validate_on_submit():
            try:
                account.create(form_user)
                user = account.get_one({"username": form.username.data, "point": form.point.data})
                user['_id'] = str(user['_id'])
                user['point'] = int(user['point'])
                if events_join:
                    events_join = events_join.split('|')
                    for event in events_join:
                        event_data = event_model.get_one({'_id': ObjectId(event)})
                        turn_roll = user['point'] // int(event_data['point_exchange'])
                        input_data = {
                            'user_id': user['_id'],
                            'event_id': event,
                            'turn_roll': turn_roll
                        }
                        join_event_model.create(input_data)
                print(f"Created successfully {form_user['username']}.")
                flash(f"Tạo thành công tài khoản '{form_user['username']}'.", "success")
                return redirect(url_for('home'))
            except Exception as e:
                print(f"Error.\n{e}")
                flash('Server gặp sự cố, vui lòng thử lại sau.', 'warning')
                return redirect(url_for('home'))
    else:
        return render_template('admin/account/create.html', title='Create account', form=form, events=events)


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
    for event in events:
        event['_id'] = str(event['_id'])
        if event['_id'] not in event_join:
            event_not_join.append(event)
        else:
            event_join.pop(event['_id'])
            event_join.update({event['_id']: {'event_name': event['event_name']}})
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
        events_join = form.join_event.data
        form_data = {
            "username": str(form.username.data).lower(),
            "usercode": form.usercode.data,
            "point": form.point.data,
            "is_active": form.is_active.data,
            "date_updated": datetime.utcnow()
        }

        if form.validate_on_submit():
            if 'date_updated' not in user:
                account.update(ObjectId(_id), {'date_updated': ''})
            try:
                edit_account = account.update(ObjectId(_id), form_data)
                user['point'] = int(user['point'])
                if events_join:
                    events_join = events_join.split('|')
                    print("Event join: ", events_join)
                    for event in events_join:
                        print("Event each: ", event)
                        event_data = event_model.get_one({'_id': ObjectId(event)})
                        print("Event data: ", event_data)
                        turn_roll = user['point'] // int(event_data['point_exchange'])
                        print("Turn roll: ", turn_roll)
                        input_data = {
                            'user_id': user['_id'],
                            'event_id': event,
                            'turn_roll': turn_roll
                        }
                        print("Input data: ", input_data)
                        has_exists = join_event_model.get_one({'event_id': event[0], 'user_id': _id})
                        if has_exists is None:
                            join_event_model.create(input_data)
                        else:
                            join_event_model.update(has_exists['_id'], input_data)
                flash(f'Cập nhật tài khoản "{edit_account["username"]}".', 'success')
                return redirect(url_for('admin.account_manager'))
            except Exception as e:
                print('Error when editing account.', e)
                flash('Server gặp sự cố, vui lòng thử lại sau.', 'warning')
                return redirect(url_for('admin.account_manager'))
        flash('Một số thông tin bị lỗi, vui lòng kiểm tra lại.', 'warning')
        return redirect(url_for('admin.account_edit'))
    return render_template(
        'admin/account/edit.html',
        form=form, account=user,
        _id=user['_id'],
        events=event_not_join,
        event_join=event_join
    )

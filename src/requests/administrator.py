from _datetime import datetime
from bson import ObjectId
from flask import render_template, redirect, request, flash, url_for, Blueprint, session
from .authenticate import admin_authorize, authorize_user
from ..forms import CreateAccountForm, UpdateAccountForm
from ..models import Models
from ..mongodb import ACCOUNT_TABLE
from ..utils.utilities import role_auth_id, validate_account_create

import bcrypt

admin = Blueprint('admin', __name__)
account = Models(table=ACCOUNT_TABLE)


@admin.route('/accounts/')
def account_manager():
    adm = admin_authorize()
    if not adm:
        flash("You're not allow to access this page.", 'danger')
        return redirect(url_for('home'))
    account_data = account.get_many()
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
        flash("You're not allow to access this page.", 'danger')
        return redirect(url_for('home'))
    form = CreateAccountForm()
    if request.method == 'POST':
        password = form.password.data.encode("utf-8")
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

        form_data = {
            "username": form.username.data,
            "email": form.email.data,
            "password": hashed_password,
            "turn_roll": form.turn_roll.data,
            "role_id": role_auth_id,
            "is_active": True,
            "date_created": datetime.utcnow()
        }

        validate_account_create(form_data['email'], form_data['username'], form_data['turn_roll'])

        if form.validate_on_submit():
            try:
                account.create(form_data)
                # session auto login after register
                # session["username"] = username
                print(f"Created successfully {form_data['username']}.")
                flash(f"Account '{form_data['username']}' creating successful.", "success")
                return redirect(url_for('home'))
            except Exception as e:
                print(f"Error.\n{e}")
                flash('Server gặp sự cố, vui lòng thử lại sau.', 'warning')
                return redirect(url_for('home'))
    else:
        return render_template('admin/account/create.html', title='Create account', form=form)


@admin.route('account/<string:_id>', methods=['POST', 'GET'])
def account_edit(_id):
    adm = admin_authorize()
    if not adm:
        flash("You're not allow to access this page.", 'danger')
        return redirect(url_for('home'))
    form = UpdateAccountForm()
    user = account.get_one({'_id': ObjectId(_id)})
    if not user:
        flash('Account not found.', 'warning')
        return redirect(url_for('home'))
    if request.method == 'GET':
        return render_template('admin/account/edit.html', form=form, account=user, _id=user['_id'])
    elif request.method == 'POST':

        form_data = {
            "username": form.username.data,
            "email": form.email.data,
            "turn_roll": form.turn_roll.data,
            "is_active": form.is_active.data,
            "date_updated": datetime.utcnow()
        }

        if form.validate_on_submit():
            if 'date_updated' not in user:
                account.update(ObjectId(_id), {'date_updated': ''})
            try:
                edit_account = account.update(ObjectId(_id), form_data)
                print(f'{edit_account["date_updated"]}Successful editing account.')
                print(edit_account)
                flash(f'Update tài khoản "{edit_account["username"]}".', 'success')
                return redirect(url_for('admin.account_manager'))
            except Exception as e:
                print('Error when editing account.', e)
                flash('Server gặp sự cố, vui lòng thử lại sau.', 'warning')
                return redirect(url_for('admin.account_manager'))
        flash('Một số thông tin bị lỗi, vui lòng kiểm tra.', 'warning')
        return render_template('admin/account/edit.html', form=form, account=user, _id=user['_id'])
    flash('Method not allowed.', 'danger')
    return render_template('admin/account/edit.html', form=form, account=user, _id=user['_id'])

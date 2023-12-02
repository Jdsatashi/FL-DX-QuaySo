from _datetime import datetime
from bson import ObjectId
from flask import render_template, redirect, request, flash, url_for, Blueprint, session
from .authenticate import admin_authorize
from ..forms import CreateAccountForm
from ..mongodb import ACCOUNT_TABLE
from ..utils.utilities import role_auth_id, validate_account_value

import bcrypt

admin = Blueprint('admin', __name__)


@admin.route('/accounts/')
def account_manager():
    adm = admin_authorize()
    if not adm:
        flash("You're not allow to access this page.", 'danger')
        return redirect(url_for('home'))
    account_data = ACCOUNT_TABLE.find()
    try:
        data_list = list(account_data)
        for data in data_list:
            data.pop('password')
            data['_id'] = str(data['_id'])
            data['role_id'] = str(data['role_id'])
        # data.append()
        print(data_list)
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

        validate_account_value(form_data['email'], form_data['username'], form_data['turn_roll'])

        if form.validate_on_submit():
            try:
                ACCOUNT_TABLE.insert_one(form_data)
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
    form = CreateAccountForm()
    if request.method == 'GET':
        return render_template('admin/account/edit.html', form=form)
    elif request.method == 'POST':
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

        validate_account_value(form_data['email'], form_data['username'], form_data['turn_roll'])

        if form.validate_on_submit():
            edit_account = ACCOUNT_TABLE.find_one_and_update(
                {'_id': ObjectId(_id)},
                {
                    '$set': form_data
                }
            )
            if not edit_account:
                print('Error when editing account.')
                flash('Server gặp sự cố, vui lòng thử lại sau.', 'warning')
                return redirect(url_for('admin.account_manager'))

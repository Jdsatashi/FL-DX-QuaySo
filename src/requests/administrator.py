from _datetime import datetime
from bson import ObjectId
from flask import render_template, redirect, request, flash, url_for, Blueprint, session
import validators
from .authenticate import admin_authorize
from ..forms import CreateAccountForm
from ..mongodb import ACCOUNT_TABLE
from ..utils.utilities import role_auth_id, role_admin_id

import validators
import bcrypt


admin = Blueprint('admin', __name__)


@admin.route('/accounts/')
def account_manager():
    adm = admin_authorize
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
    form = CreateAccountForm()
    if request.method == 'POST':
        username = form.username.data
        emails = form.email.data
        password = form.password.data.encode("utf-8")
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
        turn_roll = form.turn_roll.data
        is_active = True

        if not validators.email(emails):
            flash(f"Email was not valid.", "warning")
            return redirect(url_for('admin.account_create'))
        if ACCOUNT_TABLE.find_one(username):
            flash(f"Username of Email.", "warning")
            return redirect(url_for('admin.account_create'))
        if ACCOUNT_TABLE.find_one(emails):
            flash(f"Email {emails} was used.", "warning")
            return redirect(url_for('admin.account_create'))
        if isinstance(turn_roll, int):
            flash(f"Lượt quay phải là số.", "warning")
            return redirect(url_for('admin.account_create'))

        if form.validate_on_submit():
            try:
                ACCOUNT_TABLE.insert_one({
                    "username": username,
                    "email": emails,
                    "password": hashed_password,
                    "turn_roll": turn_roll,
                    "role_id": role_auth_id,
                    "is_active": is_active,
                    "date_created": datetime.utcnow()
                })
                # session auto login after register
                # session["username"] = username
                flash(f"Account '{username}' creating successful.", "success")
                return redirect(url_for('home'))
            except Exception as e:
                print(f"Error.\n{e}")
                flash('Server gặp sự cố, vui lòng thử lại sau.', 'warning')
                return redirect(url_for('home'))
    else:
        return render_template('auth/register.html', title='Register', form=form)

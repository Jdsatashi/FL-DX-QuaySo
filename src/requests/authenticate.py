
from bson import ObjectId
from flask import render_template, redirect, request, flash, url_for, Blueprint, session
import bcrypt
from src.forms import LoginForm, UpdatePasswordForm
from ..mongodb import ACCOUNT_TABLE
from ..utils.utilities import role_auth_id, role_admin_id

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        username = form.username.data
        password = form.password.data.encode("utf-8")
        user = ACCOUNT_TABLE.find_one({
            "username": username
        })
        if form.validate_on_submit():
            if not user:
                flash(f"Username '{username}' is not found.", "warning")
                return redirect(url_for('auth.login'))
            if user and bcrypt.checkpw(password, user["password"]):
                is_role = user.get("role_id")
                if is_role is None:
                    ACCOUNT_TABLE.find_one_and_update({
                        '_id': ObjectId(user["_id"])
                    }, {
                        '$set': {
                            "role_id": role_auth_id
                        }
                    })
                session["username"] = username
                session["_id"] = user["_id"]
                flash(f"Successfully Login! Welcome '{username}'.", "success")
                return redirect(url_for('home'))
            else:
                flash(f"Password was incorrect.", "danger")
                return redirect(url_for('auth.login'))
    else:
        return render_template('auth/login.html', title='Login', form=form)


@auth.route('/logout')
def logout():
    session.pop('username')
    return redirect(url_for('home'))


@auth.route('account/reset-password/<string:_id>', methods=['GET'])
def reset_password(_id):
    user = authorize_user()
    is_admin = admin_authorize()
    form = UpdatePasswordForm()
    print("Reset password function")
    if user['_id'] == _id:
        print(f'User edit: {user}')
        return render_template('auth/reset_password.html', account=user, form=form)
    elif is_admin:
        account = ACCOUNT_TABLE.find_one({'_id': ObjectId(_id)})
        print(f'Admin edit: {user}')
        return render_template('auth/reset_password.html', form=form, account=account)
    else:
        print('Not access able.')
    return redirect(url_for('admin.account_manager'))


def authorize_user():
    if 'username' in session:
        account_data = ACCOUNT_TABLE.find_one(
            {'username': session['username']})
        account_data['_id'] = str(account_data['_id'])
        data = account_data
        if 'password' in data:
            data.pop('password')
        return data
    else:
        return False


def admin_authorize():
    user_data = authorize_user()
    if not user_data:
        return False
    user_data['_id'] = str(user_data['_id'])
    user = user_data
    if 'password' in user:
        user.pop('password')
    is_role_admin = user['role_id']
    if not is_role_admin == role_admin_id:
        print(
            f"Test role false: \nUser role: {is_role_admin}\nAdmin role: {role_admin_id}")
        return False
    return user_data

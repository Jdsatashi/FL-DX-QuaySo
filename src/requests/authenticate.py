from bson import ObjectId
from flask import render_template, redirect, request, flash, url_for, Blueprint, session
import bcrypt
from src.forms import LoginForm, UpdatePasswordForm
from src.models import Models
from src.mongodb import ACCOUNT_TABLE
from src.utils.utilities import role_auth_id, role_admin_id

auth = Blueprint('auth', __name__)
account = Models(table=ACCOUNT_TABLE)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        username = form.username.data
        password = form.password.data.encode("utf-8")
        user = account.get_one({'username': username})
        if form.validate_on_submit():
            if not user:
                flash(f"Username '{username}' is not found.", "warning")
                return redirect(url_for('auth.login'))
            if user and bcrypt.checkpw(password, user["password"]):
                is_role = user["role_id"]
                if is_role is None or is_role == '':
                    print('update role')
                    account.update(ObjectId(user["_id"]), {'role_id': role_auth_id})
                session["username"] = username
                user['_id'] = str(user["_id"])
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
    if 'username' in session:
        session.pop('username')
        return redirect(url_for('home'))
    return redirect(url_for('home'))


@auth.route('account/reset-password/<string:_id>', methods=['GET', 'POST'])
def reset_password(_id):
    user = authorize_user()
    is_admin = admin_authorize()
    form = UpdatePasswordForm()
    print("Reset password function")
    if user['_id'] == _id:
        if request.method == 'POST':
            password = form.new_password.data
            hash_password = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
            account.update(ObjectId(_id), {'password': hash_password})
            flash(f"Successfully update password'.", "success")
            return redirect(url_for('home'))
        return render_template('auth/reset_password.html', account=user, form=form)
    elif is_admin:
        user = account.get_one(ObjectId(_id))
        if request.method == 'POST':
            password = form.new_password.data
            hash_password = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
            update_data = {
                'password': hash_password
            }
            account.update(ObjectId(_id), update_data)
            flash(f"Successfully update password for {user['username']}.", "success")
            return redirect(url_for('home'))
        return render_template('auth/reset_password.html', form=form, account=user)
    else:
        print('Not access able.')
    return redirect(url_for('admin.account_manager'))


def authorize_user():
    if 'username' in session:
        account_data = account.get_one({'username': session['username']})
        if account_data is None:
            session.pop('username')
            return authorize_user()
        account_data['_id'] = str(account_data['_id'])
        data = account_data
        if 'password' in data:
            data.pop('password')
        return data
    else:
        return False


def admin_authorize():
    user = authorize_user()
    if not user:
        return False
    if 'password' in user:
        user.pop('password')
    is_role_admin = user['role_id']
    if not is_role_admin == role_admin_id:
        print(
            f"Test role false: \nUser role: {is_role_admin}\nAdmin role: {role_admin_id}")
        return False
    return user

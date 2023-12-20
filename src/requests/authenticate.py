from bson import ObjectId
from flask import render_template, redirect, request, flash, url_for, Blueprint, session
import bcrypt
from markupsafe import Markup

from src.forms import LoginForm, UpdatePasswordForm, UpdateInfoAccountForm
from src.logs import message_logger
from src.models import Models
from src.mongodb import ACCOUNT_TABLE
from src.utils.utilities import role_auth_id, role_admin_id

auth = Blueprint('user', __name__)
account = Models(table=ACCOUNT_TABLE)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        username = str(form.username.data).lower()
        password = form.password.data.encode("utf-8")
        user = account.get_one({'username': username})
        if form.validate_on_submit():
            if not user:
                flash(f"Tài khoản '{username}' không tồn tại.", "warning")
                return redirect(url_for('user.login'))
            if user and bcrypt.checkpw(password, user["password"]):
                is_role = user["role_id"]
                if is_role is None or is_role == '':
                    account.update(ObjectId(user["_id"]), {'role_id': role_auth_id})
                session["username"] = username
                user['_id'] = str(user["_id"])
                session["_id"] = user["_id"]
                flash(f"Đăng nhập thành công, xin chào '{username.upper()}'.", "success")
                message_logger.info(f"User '{username.upper()}' đã đăng nhập.")
                return redirect(url_for('home'))
            else:
                flash(f"Mật khẩu không đúng, vui lòng thử lại.", "warning")
                return redirect(url_for('user.login'))
    else:
        return render_template('user/login.html', title='Login', form=form)


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
    if user['_id'] == _id:
        if request.method == 'POST':
            password = form.new_password.data
            hash_password = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
            account.update(ObjectId(_id), {'password': hash_password})
            flash(f"Cập nhật nhật khẩu mới thành công.", "success")
            message_logger.info(f"User '{user['username']}' đã thay đổi password.")
            return redirect(url_for('home'))
        return render_template('user/reset_password.html', account=user, form=form)
    elif is_admin:
        user = account.get_one(ObjectId(_id))
        if request.method == 'POST':
            password = form.new_password.data
            hash_password = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
            update_data = {
                'password': hash_password
            }
            account.update(ObjectId(_id), update_data)
            flash(f"Cập nhật mật khẩu thành công cho user: {user['username']}.", "success")
            message_logger.info(f"Admin đã thay đổi password cho user '{user['username']}'.")
            return redirect(url_for('home'))
        return render_template('user/reset_password.html', form=form, account=user)
    else:
        print('Not access able.')
        return redirect(url_for('home'))


@auth.route('/thong-tin/<string:_id>', methods=['GET', 'POST'])
def information(_id):
    user = authorize_user()
    if not user:
        flash(Markup(f'Bạn phải đăng nhập để chọn sự kiện quay số. <strong><a href="{url_for("auth.login")}" style="color: '
                     '#3a47a6">Click để đăng nhập</a></strong>'), 'warning')
        return redirect(url_for('home'))
    form = UpdateInfoAccountForm()
    if request.method == 'POST':
        pass
    else:
        return render_template('user/infomation.html', user=user, form=form)


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

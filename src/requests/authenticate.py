from datetime import timedelta
from bson import ObjectId
from flask import render_template, redirect, request, flash, url_for, Blueprint, session
from markupsafe import Markup

from src.app import app
from src.forms import LoginForm, UpdatePasswordForm, UpdateInfoAccountForm
from src.logs import message_logger, logger
from src.models import Models
from src.mongodb import ACCOUNT_TABLE
from src.utils.utilities import role_auth_id, role_admin_id

import bcrypt


auth = Blueprint('user', __name__)
account = Models(table=ACCOUNT_TABLE)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        username = str(form.username.data)
        password = form.password.data.encode("utf-8")
        remember_me = form.remember_me.data
        user = account.get_one({'username': {"$regex": username, "$options": "i"}})
        if form.validate_on_submit():
            if not user:
                flash(f"Tài khoản không tồn tại.", "warning")
                return redirect(url_for('user.login'))
            if bcrypt.checkpw(password, user["password"]):
                COOKIE_MAX_AGE = 7 * 24 * 3600 if remember_me else 12 * 3600
                if "role_id" not in user:
                    account.update(ObjectId(user["_id"]), {'role_id': role_auth_id})
                session["username"] = user['username']
                if user['role_id'] == role_admin_id:
                    session['is_admin'] = True
                user['_id'] = str(user["_id"])
                session["_id"] = user["_id"]
                session.permanent = True
                app.permanent_session_lifetime = timedelta(seconds=COOKIE_MAX_AGE)
                flash(f"Đăng nhập thành công, xin chào '{username.upper()}'.", "success")
                message_logger.info(f"User '{username.upper()}' đã đăng nhập.")
                logger.info(f"User '{username.upper()}' đã đăng nhập.")
                return redirect(url_for('home'))
            else:
                flash(f"Mật khẩu không đúng, vui lòng thử lại.", "warning")
                return redirect(url_for('user.login'))
        flash(f"Một số dữ liệu không đúng, vui lòng tử lại.", "warning")
        return redirect(url_for('user.login'))
    else:
        return render_template('user/login.html', form=form, title="Đăng nhập")


@auth.route('/logout')
def logout():
    if 'username' in session:
        session.pop('username')
        return redirect(url_for('home'))
    return redirect(url_for('home'))


@auth.route('account/reset-password/<string:_id>', methods=['GET', 'POST'])
def reset_password(_id):
    user = authorize_user()
    if not user:
        flash(Markup(f'Bạn phải đăng nhập để thay đổi mật khẩu. <strong><a href="{url_for("user.login")}" style="color: '
                     '#3a47a6">Click để đăng nhập</a></strong>'), 'warning')
        return redirect(url_for('home'))
    is_admin = admin_authorize()
    form = UpdatePasswordForm()
    if user['_id'] == _id or is_admin:
        if request.method == 'POST':
            password = form.new_password.data
            hash_password = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
            if form.validate_on_submit():
                try:
                    account.update(ObjectId(_id), {'password': hash_password})
                    if user['_id'] == _id:
                        flash(f"Cập nhật nhật khẩu mới thành công.", "success")
                        message_logger.info(f"User '{user['username']}' đã thay đổi password.")
                        return redirect(url_for('home'))
                    elif is_admin:
                        flash(f"Cập nhật mật khẩu thành công cho user: {user['username']}.", "success")
                        message_logger.info(f"Admin đã thay đổi password cho user '{user['username']}'.")
                        return redirect(url_for('home'))
                except Exception as e:
                    logger.error(f"Error while reset password.\n{e}")
                    return redirect(url_for('home'))
        return render_template('user/reset_password.html', account=user, form=form, title="Đổi mật khẩu")
    else:
        logger.info(f"User {user['username']} try to reset password of user {_id}")
        flash(f"Không được phép truy cập.", "warning")
        return redirect(url_for('home'))


@auth.route('/thong-tin')
@auth.route('/thong-tin/')
def fake_thong_tin():
    user = authorize_user()
    if not user:
        flash(Markup(
            f'Bạn phải đăng nhập để xem thông tin cá nhân. <strong><a href="{url_for("user.login")}" style="color: '
            '#3a47a6">Click để đăng nhập</a></strong>'), 'warning')
        return redirect(url_for('home'))
    return redirect(url_for('home'))


@auth.route('/thong-tin/<string:_id>', methods=['GET', 'POST'])
def information(_id):
    user = authorize_user()
    if not user:
        flash(Markup(f'Bạn phải đăng nhập để xem thông tin cá nhân. <strong><a href="{url_for("user.login")}" style="color: '
                     '#3a47a6">Click để đăng nhập</a></strong>'), 'warning')
        return redirect(url_for('home'))
    form = UpdateInfoAccountForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                form_data = {
                    'fullname': form.fullname.data,
                    'email': form.email.data,
                    'phone': form.phone.data,
                    'address': form.address.data,
                }
                account.update(ObjectId(_id), form_data)
                message_logger.info(f"User {user['username']} cập nhật thông tin cá nhân thành công")
                flash(f"Cập nhật thông tin tài khoản thành công.", "success")
                return redirect(url_for('user.information', _id=_id))
            except Exception as e:
                logger.error(f"Error when add info: {e}")
                flash(f"Cập nhật thông tin thất bại.", "warning")
                return redirect(url_for('user.information', _id=_id))
    else:
        return render_template('user/information.html', user=user, form=form, title="Thông tin tài khoản")


# function for authorize if user
def authorize_user():
    if 'username' in session:
        account_data = account.get_one({'username': session['username']})
        if account_data is None:
            session.pop('username')
            return authorize_user()
        account_data['_id'] = str(account_data['_id'])
        # Remove sensitive data password
        if 'password' in account_data:
            account_data.pop('password')
        return account_data
    else:
        return False


# function for authorize if admin
def admin_authorize():
    # authorize user first
    user = authorize_user()
    if not user:
        return False
    if 'password' in user:
        user.pop('password')
    # Compare if role_id of user is = role_id of role admin
    is_role_admin = user['role_id']
    if not is_role_admin == role_admin_id:
        print(
            f"Test role false: \nUser role: {is_role_admin}\nAdmin role: {role_admin_id}")
        return False
    return user

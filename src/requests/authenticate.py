from datetime import timedelta
from bson import ObjectId
from flask import render_template, redirect, request, flash, url_for, Blueprint, session
from markupsafe import Markup

from src.app import app, message_logger, logger
from src.forms import LoginForm, UpdatePasswordForm, UpdateInfoAccountForm
from src.utils.constants import user_model
from src.utils.utilities import role_auth_id, role_admin_id

import bcrypt

auth = Blueprint('user', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    # Get data form
    form = LoginForm()
    # Process login
    if request.method == 'POST':
        # Get data of user for prepare login
        username = str(form.username.data)
        password = form.password.data.encode("utf-8")
        remember_me = form.remember_me.data
        # Try get user depend on username
        user = user_model.get_one({'username': {"$regex": username, "$options": "i"}})
        # If form validated and submit
        if form.validate_on_submit():
            # Check if user with user is existing
            if not user:
                flash(f"Tài khoản không tồn tại.", "warning")
                return redirect(url_for('user.login'))
            # If username existed, then check password
            if bcrypt.checkpw(password, user["password"]):
                # Create life-time for cookie
                COOKIE_MAX_AGE = 7 * 24 * 3600 if remember_me else 12 * 3600
                # Add default user role if user not has a role
                if "role_id" not in user:
                    user_model.update(ObjectId(user["_id"]), {'role_id': role_auth_id})
                message_logger.info(f"User '{username.upper()}' đã đăng nhập.")
                # Print and show message when login successful
                logger.info(f"User '{username.upper()}' đã đăng nhập.")
                flash(f"Đăng nhập thành công, xin chào '{username.upper()}'.", "success")
                # Check if user is admin
                if user['role_id'] == role_admin_id:
                    session['is_admin'] = True
                # Add session username as signed
                session["username"] = user['username']
                # Add require session data
                user['_id'] = str(user["_id"])
                session["_id"] = user["_id"]
                # Session.permanent allow browser of user save session for forever or outdated session
                session.permanent = True
                # Set the lifetime of session
                app.permanent_session_lifetime = timedelta(seconds=COOKIE_MAX_AGE)
                return redirect(url_for('home'))
            # Return with error when password wrong
            else:
                flash(f"Mật khẩu không đúng, vui lòng thử lại.", "warning")
                return redirect(url_for('user.login'))
        # Return message if form not valid
        flash(f"Một số dữ liệu không đúng, vui lòng tử lại.", "warning")
        return redirect(url_for('user.login'))
    # Render template if method = GET
    else:
        return render_template('user/login.html', form=form, title="Đăng nhập")


@auth.route('/logout')
def logout():
    # Remove username and other session data
    if 'username' in session:
        message_logger.info(f"User {session['username']} đã logout.")
        session.pop('username')
        session.clear()
        return redirect(url_for('home'))
    return redirect(url_for('home'))


@auth.route('account/reset-password/<string:_id>', methods=['GET', 'POST'])
def reset_password(_id):
    user = authorize_user()
    if not user:
        flash(
            Markup(f'Bạn phải đăng nhập để thay đổi mật khẩu. <strong><a href="{url_for("user.login")}" style="color: '
                   '#3a47a6">Click để đăng nhập</a></strong>'), 'warning')
        return redirect(url_for('home'))
    logger.info(f"User change password: {user}")
    is_admin = admin_authorize()
    logger.info(f"Authorize admin: {is_admin}")
    form = UpdatePasswordForm()
    if user['_id'] == _id or is_admin:
        if request.method == 'POST':
            password = form.new_password.data
            hash_password = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
            if form.validate_on_submit():
                try:
                    user_model.update(ObjectId(_id), {'password': hash_password})
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
        flash(Markup(
            f'Bạn phải đăng nhập để xem thông tin cá nhân. <strong><a href="{url_for("user.login")}" style="color: '
            '#3a47a6">Click để đăng nhập</a></strong>'), 'warning')
        return redirect(url_for('home'))
    form = UpdateInfoAccountForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                form_data = {
                    'email': form.email.data,
                    'phone': form.phone.data,
                    'address': form.address.data,
                }
                user_model.update(ObjectId(_id), form_data)
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
        account_data = user_model.get_one({'username': session['username']})
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
    if not user['role_id'] == role_admin_id:
        return False
    return user

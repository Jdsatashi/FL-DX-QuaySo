from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField, BooleanField, IntegerField, DateField, FileField
from wtforms.validators import DataRequired, EqualTo, Length, NumberRange
from _datetime import datetime


class CreateAccountForm(FlaskForm):
    username = StringField("Username", validators=[Length(min=2), DataRequired()])
    usercode = StringField("Mã khách hàng", validators=[DataRequired()])
    password = PasswordField("Mật khẩu", validators=[Length(min=2), DataRequired()])
    confirm_password = PasswordField("Xác nhận mật khẩu", validators=[EqualTo('password'), DataRequired()])
    join_event = StringField()
    submit = SubmitField("Tạo tài khoản")


class UpdateAccountForm(FlaskForm):
    username = StringField("Tài khoản", validators=[Length(min=2), DataRequired()])
    usercode = StringField("Mã khách hàng", validators=[DataRequired()])
    join_event = StringField()
    is_active = BooleanField("Hoạt động")
    submit = SubmitField("Cập nhật tài khoản")


class UpdatePasswordForm(FlaskForm):
    new_password = PasswordField("Mật khẩu mới", validators=[Length(min=2), DataRequired()])
    confirm_password = PasswordField("Xác nhận", validators=[EqualTo('new_password'), DataRequired()])
    submit = SubmitField("Cập nhật mật khẩu")


class UpdateInfoAccountForm(FlaskForm):
    fullname = StringField("Họ và tên")
    phone = StringField("SĐT", validators=[Length(max=13)])
    address = StringField("Địa chỉ")
    email = EmailField("Email")
    submit = SubmitField("Cập nhật tài khoản")


class LoginForm(FlaskForm):
    username = StringField("Tài khoản", validators=[Length(min=1), DataRequired()])
    password = PasswordField("Mật khẩu", validators=[Length(min=2), DataRequired()])
    remember_me = BooleanField("Lưu đăng nhập")
    submit = SubmitField("Đăng nhập")


class NumberSelectedForm(FlaskForm):
    number = StringField("", validators=[DataRequired()])
    submit = SubmitField("Xác nhận")


class EventForm(FlaskForm):
    name = StringField("Tên sự kiện", validators=[DataRequired()])
    date_start = DateField("Ngày bắt đầu", default=datetime.today)
    date_close = DateField("Ngày kết thúc", validators=[DataRequired()])
    repeat_limit = IntegerField("Giới hạn lặp số", default="1", validators=[NumberRange(min=1)])
    point_exchange = IntegerField("Điểm / tem", validators=[DataRequired(), NumberRange(min=1)])
    # desc_file = FileField("Chi tiết sự kiện, file PDF")
    # desc_image = FileField("Hình ảnh")
    is_active = BooleanField("Hoạt động")
    submit = SubmitField("Xác nhận")

from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField, BooleanField, IntegerField, DateField
from wtforms.validators import DataRequired, EqualTo, Length


class CreateAccountForm(FlaskForm):
    username = StringField("Username", validators=[Length(min=2), DataRequired()])
    email = EmailField("Email", validators=[DataRequired()])
    password = PasswordField("Mật khẩu", validators=[Length(min=2), DataRequired()])
    confirm_password = PasswordField("Xác nhận mật khẩu", validators=[EqualTo('password'), DataRequired()])
    join_event = StringField()
    submit = SubmitField("Tạo tài khoản")


class UpdateAccountForm(FlaskForm):
    username = StringField("Username", validators=[Length(min=2), DataRequired()])
    email = EmailField("Email", validators=[DataRequired()])
    is_active = BooleanField("Hoạt động")
    submit = SubmitField("Cập nhật tài khoản")


class UpdatePasswordForm(FlaskForm):
    new_password = PasswordField("Mật khẩu mới", validators=[Length(min=2), DataRequired()])
    confirm_password = PasswordField("Xác nhận mật khẩu mới", validators=[EqualTo('new_password'), DataRequired()])
    submit = SubmitField("Cập nhật mật khẩu")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[Length(min=1), DataRequired()])
    password = PasswordField("Mật khẩu", validators=[Length(min=2), DataRequired()])
    remember_me = BooleanField("Lưu đăng nhập")
    submit = SubmitField("Đăng nhập")


class NumberSelectedForm(FlaskForm):
    user_id = StringField()
    event_id = StringField()
    number = StringField("", validators=[DataRequired()])
    submit = SubmitField("Xác nhận")


class EventForm(FlaskForm):
    name = StringField("Tên sự kiện", validators=[DataRequired()])
    date_close = DateField("Ngày kết thúc", validators=[DataRequired()])
    repeat_limit = IntegerField("Giới hạn lặp số")
    submit = SubmitField("Xác nhận")

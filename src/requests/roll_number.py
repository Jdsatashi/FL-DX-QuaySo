from flask import render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from _datetime import datetime

from src.mongodb import ROLL_TABLE
from src import app
from src.requests.authenticate import authorize_user


class NumberSelectedForm(FlaskForm):
    number = StringField(validators=[DataRequired()])
    submit = SubmitField("Xác nhận")


def create_number_list():
    list_number = []
    for i in range(1000):
        if not i == 0:
            list_number.append(i)
    return list_number


@app.route('/quay-so/')
def roll_number():
    form = NumberSelectedForm()
    number_list = create_number_list()
    print('Refresh page.')
    return render_template('roll_number.html', number_list=number_list, title="Quay số", form=form)


@app.route('/quay-so/chon-so/', methods=['POST'])
def selecting_number():
    user = authorize_user()
    form = NumberSelectedForm()
    if user:
        number = request.form.get('number')
        if form.validate_on_submit():
            try:
                ROLL_TABLE.insert_one({
                    'select_number': number,
                    'user_id': user['_id'],
                    'date_created': datetime.utcnow()
                })
                print('Send data successful.')
                flash(f"Chọn thành công các số {number}.", "success")
                return redirect(url_for('home'))
            except Exception as e:
                print(f'There some error while inserting to MongoDb.\n{e}')
                flash(f"Máy chủ đang gặp sự cố, vui lòng thử lại sau.", "warning")
                return redirect(url_for('selecting_number'))
    flash(f"Bạn chưa đăng nhập.", "danger")
    return redirect(url_for('home'))

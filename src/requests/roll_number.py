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
    roll_data = ROLL_TABLE.find()
    selected_number = list()
    all_number = []
    if roll_data:
        for roll in roll_data:
            roll['_id'] = str(roll['_id'])
            selected_number.append(roll['select_number'])
    for number in selected_number:
        arr = number.split(',')
        for i in arr:
            all_number.append(int(i))
    all_number.sort()
    print(all_number)
    for i in range(1000):
        if i != 0:
            list_number.append(i)
        # if i != all_number[0] and i != 0:
        #
        # else:
        #     all_number.pop(0)
        #     print(f'remove {i}')
    return list_number


@app.route('/quay-so/')
def roll_number():
    user = authorize_user()
    if not user:
        flash(f"Bạn phải đăng nhập để quay số", 'warning')
        return redirect(url_for('home'))
    user_id = user['_id']
    roll_data = ROLL_TABLE.find_one({'user_id': user_id})
    if roll_data:
        roll_data['_id'] = str(roll_data['_id'])
    print(user)
    print(roll_data)
    if 'select_number' in roll_data:
        select_number = roll_data['select_number']
        print(select_number)
        list_select_number = select_number.split(',')
        print(list_select_number)
        if str(4) in select_number:
            print('4 is selected')
        # select_number
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

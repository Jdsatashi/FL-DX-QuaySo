from flask import render_template, request, redirect, url_for, flash
from _datetime import datetime

from src.forms import NumberSelectedForm
from src.models import Models
from src.mongodb import ROLL_TABLE
from src import app
from src.requests.authenticate import authorize_user

roll_model = Models(table=ROLL_TABLE)


def create_number_list():
    list_number = []
    roll_data = roll_model.get_many()
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
        if i in all_number:
            count = 0
            while i in all_number:
                count += 1
                all_number.remove(i)
            print(f'remove {i}')
        elif i == 0:
            pass
        else:
            list_number.append(i)
    return list_number


@app.route('/quay-so/')
def roll_number():
    user = authorize_user()
    if not user:
        flash(f"Bạn phải đăng nhập để quay số", 'warning')
        return redirect(url_for('home'))
    roll_data = roll_model.get_one({'user_id': user['_id']})
    if roll_data:
        roll_data['_id'] = str(roll_data['_id'])
    list_select_number = list()
    if 'select_number' in roll_data:
        select_number = roll_data['select_number']
        list_select_number = select_number.split(',')
        # select_number
    form = NumberSelectedForm()
    number_list = create_number_list()
    print('Refresh page.')
    return render_template(
        'roll_number.html',
        number_list=number_list, title="Quay số",
        form=form,
        select_number=list_select_number,
        user=user
    )


@app.route('/quay-so/chon-so/', methods=['POST'])
def selecting_number():
    user = authorize_user()
    form = NumberSelectedForm()
    if user:
        number = request.form.get('number')
        if form.validate_on_submit():
            try:
                number_list = number.split(',')
                if len(number_list) <= int(user['turn_roll']):
                    roll_model.create({
                        'select_number': number,
                        'user_id': user['_id'],
                        'date_created': datetime.utcnow()
                    })
                    print('Send data successful.')
                    flash(f"Chọn thành công các số {number}.", "success")
                    return redirect(url_for('home'))
                print('Assign number failed.')
                flash(f"Bạn chỉ được chọn {user['turn_roll']} số.", "danger")
                return redirect(url_for('roll_number'))
            except Exception as e:
                print(f'There some error while inserting to MongoDb.\n{e}')
                flash(f"Máy chủ đang gặp sự cố, vui lòng thử lại sau.", "warning")
                return redirect(url_for('selecting_number'))
    flash(f"Bạn chưa đăng nhập.", "danger")
    return redirect(url_for('home'))

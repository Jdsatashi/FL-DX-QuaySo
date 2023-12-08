from bson import ObjectId
from flask import render_template, request, redirect, url_for, flash
from _datetime import datetime

from src.forms import NumberSelectedForm
from src.models import Models
from src.mongodb import ROLL_TABLE
from src.app import app
from src.requests.authenticate import authorize_user
from src.requests.event import event_model, join_event_model

roll_model = Models(table=ROLL_TABLE)
# roll table saving: user_id, event_id and number


def create_number_list():
    list_number = []
    # roll_data = roll_model.get_all()
    # selected_number = list()
    # all_number = []
    # if roll_data:
    #     for roll in roll_data:
    #         roll['_id'] = str(roll['_id'])
    #         selected_number.append(roll['select_number'])
    # for number in selected_number:
    #     arr = number.split(',')
    #     for i in arr:
    #         all_number.append(int(i))
    # all_number.sort()
    # print(all_number)
    # for i in range(1000):
    #     if i in all_number:
    #         count = 0
    #         while i in all_number:
    #             count += 1
    #             all_number.remove(i)
    #         print(f'remove {i}')
    #     elif i == 0:
    #         pass
    #     else:
    #         list_number.append(i)
    for i in range(1000):
        list_number.append(i+1)
    return list_number


@app.route('/chon-su-kien')
def choose_event():
    user = authorize_user()
    if not user:
        flash(f"Bạn phải đăng nhập để chọn sự kiện quay số", 'warning')
        return redirect(url_for('home'))
    events = list(event_model.get_all())
    for event in events:
        event['_id'] = str(event['_id'])
    user_joins = join_event_model.get_many({'user_id': user['_id']})
    list_joined = list()
    if user_joins:
        for user in user_joins:
            list_joined.append(user['event_id'])
    # number_list = create_number_list()
    return render_template(
        'choose_number/choose_event.html',
        user=user,
        events=events,
        event_joined=list_joined
    )


@app.route('/quay-so/<string:_id>')
def roll_number(_id):
    user = authorize_user()
    if not user:
        flash(f"Bạn phải đăng nhập để quay số", 'warning')
        return redirect(url_for('home'))
    events = event_model.get_one({'_id': ObjectId(_id)})
    print(f'Event: {events}')
    user_joins = join_event_model.get_one({'user_id': user['_id'], 'event_id': _id})
    print(f'Get user roll: {user_joins}')
    form = NumberSelectedForm()
    number_list = create_number_list()
    print('Refresh page.')
    return redirect(url_for('home'))
    # return render_template(
    #     'roll_number.html',
    #     number_list=number_list, title="Quay số",
    #     form=form,
    #     events=events,
    # )


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

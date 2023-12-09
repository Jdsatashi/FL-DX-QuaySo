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


def create_number_list():
    list_number = []
    available_number = {}
    rolled = roll_model.get_all()
    for roll in rolled:
        rolled_number = roll['selected_number'].split(',')
        list_number.append(rolled_number)
    print(list_number)
    list_number2 = []
    for i in range(1000):
        list_number2.append(i+1)
    return list_number2


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


@app.route('/quay-so/<string:_id>', methods=['POST', 'GET'])
def roll_number(_id):
    # authorize user
    user = authorize_user()
    if not user:
        flash(f"Bạn phải đăng nhập để quay số", 'warning')
        return redirect(url_for('home'))
    # Get current event to choose number
    events = event_model.get_one({'_id': ObjectId(_id)})
    # Get turn of choice number
    user_joins = join_event_model.get_one({'user_id': user['_id'], 'event_id': _id})
    # Assign turn choice for user
    user['turn_roll'] = int(user_joins['turn_roll'])
    # To string _id for compare
    user['_id'] = str(user['_id'])
    events['_id'] = str(events['_id'])

    rolled = roll_model.get_one({'user_id': user['_id'], 'event_id': _id})
    turn_chosen = 0
    number_rolled = []
    if rolled:
        number_rolled = rolled['selected_number'].split(',')
        if 'number_choices' not in rolled:
            rolled['number_choices'] = len(number_rolled)
        turn_chosen = rolled['number_choices']
    print("Rolled: ", rolled)
    # Get the form values
    form = NumberSelectedForm()
    number_list = create_number_list()
    if request.method == 'POST':
        # Get the list of number selected
        list_selected = form.number.data.split(',')
        # Validate if number selected more than turn choices
        if len(list_selected) > int(user['turn_roll']):
            flash(f"Bạn chỉ được chọn {user['turn_roll']} số.", 'danger')
            return redirect(url_for('roll_number', _id=_id))
        # Change data type of close_date value to datetime
        try:
            close_date = events['date_close'].strftime('%Y-%m-%d')
            close_date = datetime.strptime(close_date, '%Y-%m-%d')
        except AttributeError:
            close_date = datetime.strptime(events['date_close'], '%Y-%m-%d')
        # Validate if current date > closure date
        if close_date < datetime.now():
            flash(f"Sự kiện đã kết thúc 0h ngày {events['date_close'].strftime('%Y-%m-%d')}.", 'danger')
            return redirect(url_for('choose_event'))

        form_data = {
            'user_id': user['_id'],
            'event_id': events['_id'],
            'selected_number': form.number.data,
            'number_choices': len(list_selected),
            'date_created': datetime.utcnow()
        }
        if not rolled:
            try:
                roll_model.create(form_data)
                flash(f"Chọn số cho sự kiện {events['event_name']} thành công.", "success")
                return redirect(url_for('choose_event'))
            except Exception as e:
                print("Error when select number. ", e)
                flash("Lỗi server, vui lòng thử lại.")
                return redirect(url_for('choose_event'))
        else:
            try:
                roll_model.update(_id, form_data)
                flash(f"Chọn số cho sự kiện {events['event_name']} thành công.", "success")
                return redirect(url_for('choose_event'))
            except Exception as e:
                print("Error when select number. ", e)
                flash("Lỗi server, vui lòng thử lại.")
                return redirect(url_for('choose_event'))
    else:
        return render_template(
            'choose_number/choose_number.html',
            number_list=number_list, title="Quay số",
            form=form,
            events=events,
            user=user,
            _id=_id,
            turn_chosen=turn_chosen,
            number_rolled=number_rolled,
        )


@app.route('/thong-tin')
def info():
    pass

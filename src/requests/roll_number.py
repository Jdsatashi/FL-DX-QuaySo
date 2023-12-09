from bson import ObjectId
from flask import render_template, request, redirect, url_for, flash
from _datetime import datetime

from src.forms import NumberSelectedForm
from src.app import app
from src.requests.authenticate import authorize_user
from src.requests.event import event_model, join_event_model


def create_number_list(limit, event_id):
    list_selected = []
    all_number_selected = []
    unavailable_number = {}
    rolled = join_event_model.get_all()
    if rolled:
        for roll in rolled:
            print(roll)
            if 'selected_number' in roll and 'number_choices' in roll and roll['event_id'] == event_id:
                print(roll)
                list_selected.append(roll['selected_number'])
    print("List selected: ", list_selected)
    for number in list_selected:
        arr = number.split(',')
        for i in arr:
            all_number_selected.append(int(i))
    for num in all_number_selected:
        if num not in unavailable_number:
            unavailable_number[num] = 1
        else:
            unavailable_number[num] += 1
    print('Test here: ', unavailable_number)
    list_number = {}
    for i in range(1000):
        if i > 0:
            if i in unavailable_number:
                if limit - unavailable_number[i] > 0:
                    list_number[i] = limit - unavailable_number[i]
            else:
                list_number[i] = limit
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

    rolled = join_event_model.get_one({'user_id': user['_id'], 'event_id': _id})
    turn_chosen = 0
    number_rolled = []
    if 'selected_number' in rolled and 'number_choices' in rolled:
        number_rolled = rolled['selected_number'].split(',')
        if 'number_choices' not in rolled:
            rolled['number_choices'] = len(number_rolled)
        turn_chosen = rolled['number_choices']
    # Get the form values
    form = NumberSelectedForm()
    number_list = create_number_list(events['limit_repeat'], _id)
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
            'selected_number': form.number.data,
            'number_choices': len(list_selected),
            'date_created': datetime.utcnow()
        }
        if 'selected_number' not in rolled and 'number_choices' not in rolled:
            try:
                id_roll = str(rolled['_id'])
                join_event_model.update(ObjectId(id_roll), form_data)
                flash(f"Chọn số cho sự kiện {events['event_name']} thành công.", "success")
                return redirect(url_for('choose_event'))
            except Exception as e:
                print("Error when select number. ", e)
                flash("Lỗi server, vui lòng thử lại.")
                return redirect(url_for('choose_event'))
        else:
            try:
                form_data.pop('date_created')
                form_data.update({'date_updated': datetime.utcnow()})
                id_roll = str(rolled['_id'])
                join_event_model.update(ObjectId(id_roll), form_data)
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
def information():
    # authorize user
    user = authorize_user()
    if not user:
        flash(f"Bạn phải đăng nhập để xem thông tin", 'warning')
        return redirect(url_for('home'))
    data = {}
    list_event_joined = list()

    join_event = join_event_model.get_many({'user_id': user['_id']})
    for event in join_event:
        list_event_joined.append(event['event_id'])
        if 'selected_number' in event and 'number_choices' in event:
            data[event['event_id']] = {
                'turn_roll': event['turn_roll'],
                'number_choices': event['number_choices'],
                'selected_number': event['selected_number']
            }
    for id_event in list_event_joined:
        event = event_model.get_one(ObjectId(id_event))
        if id_event in data:
            data[id_event].update({
                'event_name': event['event_name'],
                'date_close': event['date_close'],
                'event_active': event['is_active']
            })
        else:
            data[id_event] = {
                'event_name': event['event_name'],
                'date_close': event['date_close'],
                'event_active': event['is_active']
            }
    return render_template('information/info.html', infos=data)

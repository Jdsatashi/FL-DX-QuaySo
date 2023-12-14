from bson import ObjectId
from flask import render_template, request, redirect, url_for, flash
from _datetime import datetime

from markupsafe import Markup

from src.forms import NumberSelectedForm
from src.app import app
from src.logs import message_logger, logger
from src.requests.authenticate import authorize_user
from src.requests.event import event_model, join_event_model


def create_number_list(limit, event_id, user_id):
    list_selected = []
    all_number_selected = []
    unavailable_number = {}
    user_selected = []
    user_rolled = join_event_model.get_one({'event_id': event_id, 'user_id': user_id})
    if 'selected_number' in user_rolled and 'number_choices' in user_rolled:
        number_selected = user_rolled['selected_number'].split(',')
        for number in number_selected:
            user_selected.append(int(number))
    rolled = join_event_model.get_all()
    if rolled:
        for roll in rolled:
            if 'selected_number' in roll and 'number_choices' in roll and roll['event_id'] == event_id:
                list_selected.append(roll['selected_number'])
    for number in list_selected:
        arr = number.split(',')
        for i in arr:
            all_number_selected.append(int(i))
    for num in all_number_selected:
        if num not in unavailable_number:
            unavailable_number[num] = 1
        else:
            unavailable_number[num] += 1
        if num in user_selected:
            unavailable_number[num] = 0
    list_number = {}
    for i in range(1000):
        if i > 0:
            if i in unavailable_number:
                if limit - unavailable_number[i] > 0 and unavailable_number[i] > 0:
                    list_number[i] = limit - unavailable_number[i]
            else:
                list_number[i] = limit
    return list_number


@app.route('/chon-su-kien')
def choose_event():
    user = authorize_user()
    if not user:
        flash(Markup('Bạn phải đăng nhập để chọn sự kiện quay số. <strong><a href="/auth/login" style="color: #3a47a6">Click để đăng nhập</a></strong>'), 'warning')
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
        flash(Markup('Bạn phải đăng nhập để chọn sự kiện quay số. <strong><a href="/auth/login" style="color: #3a47a6">Click để đăng nhập</a></strong>'), 'warning')
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
    events.update({
        'event_year': events['date_created'].year,
        'folder_path': str('uploads/' + str(events['date_created'].year) + '/' + events['event_name'])
    })
    events.pop('date_created')

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
    number_list = create_number_list(events['limit_repeat'], _id, user['_id'])
    if request.method == 'POST':
        # Get the list of number selected
        list_selected = form.number.data.split(',')
        unique_set = set(list_selected)
        list_selected = list(unique_set)
        # Validate if number selected more than turn choices
        if len(list_selected) > int(user['turn_roll']):
            flash(f"Bạn chỉ được chọn {user['turn_roll']} số.", 'warning')
            return redirect(url_for('roll_number', _id=_id))
        # Change data type of close_date value to datetime
        try:
            close_date = events['date_close'].strftime('%Y-%m-%d')
            close_date = datetime.strptime(close_date, '%Y-%m-%d')
        except AttributeError:
            close_date = datetime.strptime(events['date_close'], '%Y-%m-%d')
        # Validate if current date > closure date
        if close_date < datetime.now():
            flash(f"Sự kiện đã kết thúc 0h ngày {events['date_close'].strftime('%Y-%m-%d')}.", 'warning')
            return redirect(url_for('choose_event'))

        form_data = {
            'selected_number': form.number.data,
            'number_choices': len(unique_set),
            'date_created': datetime.utcnow()
        }
        if 'selected_number' not in rolled and 'number_choices' not in rolled:
            try:
                id_roll = str(rolled['_id'])
                join_event_model.update(ObjectId(id_roll), form_data)
                flash(
                    f"Chọn các số [{form_data['selected_number']}] cho sự kiện '{events['event_name'].upper()}' thành công.",
                    "success")
                message_logger.info(
                    f"User '{user['username']}' đã chọn [{form_data['number_choices']}] số [{form_data['selected_number']}].")
                return redirect(url_for('roll_number', _id=_id))
            except Exception as e:
                flash("Lỗi server, vui lòng thử lại.")
                logger.debug(f"Error when choosing number.\n{e}")
                return redirect(url_for('choose_event'))
        else:
            try:
                form_data.pop('date_created')
                form_data.update({'date_updated': datetime.utcnow()})
                id_roll = str(rolled['_id'])
                join_event_model.update(ObjectId(id_roll), form_data)
                flash(
                    f"Chọn các số [{form_data['selected_number']}] cho sự kiện '{events['event_name'].upper()}' thành công.",
                    "success")
                message_logger.info(
                    f"User '{user['username'].upper()}' đã cập nhật chọn [{form_data['number_choices']}] số [{form_data['selected_number']}].")
                return redirect(url_for('roll_number', _id=_id))
            except Exception as e:
                flash("Lỗi server, vui lòng thử lại.")
                logger.debug(f"Error when re choosing number.\n{e}")
                return redirect(url_for('choose_event'))
    else:
        message_logger.info(f"{user['username']} vào trang chọn số.")
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
        flash(Markup('Bạn phải đăng nhập để xem thông tin. <strong><a href="/auth/login" style="color: #3a47a6">Click để đăng nhập</a></strong>'), 'warning')
        return redirect(url_for('home'))
    data = {}
    list_event_joined = list()

    join_event = join_event_model.get_many({'user_id': user['_id']})
    for event in join_event:
        list_event_joined.append(event['event_id'])
        if 'selected_number' in event and 'number_choices' in event:
            data[event['event_id']] = {
                'turn_roll': int(event['turn_roll']),
                'number_choices': int(event['number_choices']),
                'selected_number': event['selected_number']
            }
        else:
            data[event['event_id']] = {
                'turn_roll': int(event['turn_roll'])
            }
    for id_event in list_event_joined:
        event = event_model.get_one(ObjectId(id_event))
        data[id_event].update({
            'event_name': event['event_name'],
            'date_close': event['date_close'],
            'event_active': event['is_active']
        })

    return render_template('information/info.html', infos=data)

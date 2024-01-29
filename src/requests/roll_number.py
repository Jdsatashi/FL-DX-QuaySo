import traceback

from bson import ObjectId
from flask import render_template, request, redirect, url_for, flash, jsonify
from _datetime import datetime, timedelta

from flask_weasyprint import render_pdf, HTML
from markupsafe import Markup

from src.forms import NumberSelectedForm
from src.app import app, message_logger, logger
from src.mongodb import USER_JOIN_EVENT
from src.requests.authenticate import authorize_user
from src.utils.constants import event_model, join_event_model, MAX_NUMBER_RANGE_DEFAULT as MAX_NUMBER, DATE_RANDOM, \
    RAMDOM_HOUR
from src.utils.utilities import create_number_list


@app.route('/chon-su-kien')
def choose_event():
    user = authorize_user()
    if not user:
        flash(Markup(
            f'Bạn phải đăng nhập để chọn sự kiện quay số. <strong><a href="{url_for("user.login")}" style="color: '
            f'#3a47a6">Click để đăng nhập</a></strong>'),
            'warning')
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
        event_joined=list_joined,
        title="Chọn sự kiện"
    )


@app.route('/quay-so/<string:_id>', methods=['GET', 'POST'])
def roll_number(_id):
    # authorize user
    user = authorize_user()
    if not user:
        flash(Markup(
            f'Bạn phải đăng nhập để quay số. <strong><a href="{url_for("user.login")}" style="color: '
            f'#3a47a6">Click để đăng nhập</a></strong>'),
            'warning')
        return redirect(url_for('home'))
    data = dict()
    # Get current event to choose number
    events = event_model.get_one({'_id': ObjectId(_id)})
    logger.info(f"Event data: {events}")
    # Edit element of event
    events['_id'] = str(events['_id'])
    events.pop('date_created')
    # Get range number for generating number list
    max_range = events.get('range_number', MAX_NUMBER)
    # Format date follow by day-month-year for easily readable
    date_show = datetime.strptime(events['date_close'], '%Y-%m-%d').strftime('%d-%m-%Y')
    events.update({'date_show': date_show})
    # Get data rolled if user has joined event
    rolled = join_event_model.get_one({'user_id': user['_id'], 'event_id': _id})
    # Assign turn choice for user
    user['turn_roll'] = rolled['turn_roll']
    user['point'] = rolled['user_point']
    turn_chosen = 0
    number_rolled = []
    # Check if user was rolled and add get number chosen
    if 'selected_number' in rolled and 'number_choices' in rolled:
        number_rolled = rolled['selected_number'].split(', ')
        if 'number_choices' not in rolled:
            rolled['number_choices'] = len(number_rolled)
        turn_chosen = rolled['number_choices']
    # Get the form data
    # form = NumberSelectedForm()
    form = ''
    if request.method == 'POST':
        # str_list_number = form.number.data
        str_list_number = request.json.get('list_number_selected')
        data = insert_select_number(str_list_number, user, events, rolled, max_range)
        return jsonify({
            'message': 'Roll number successfully.',
            'data': data
        })
    else:
        # Create a number list for user can choose
        number_list = create_number_list(max_range, events['limit_repeat'], _id, user['_id'])
        # Get current page for compare
        current_date = datetime.now().strftime('%Y-%m-%d')
        date_close = datetime.strptime(events['date_close'], "%Y-%m-%d")
        # Date random to take random if user didn't select number
        date_random = date_close - timedelta(days=DATE_RANDOM)
        date = date_random.strftime('%d-%m-%Y')
        # Data send to template
        data.update({
            'form': form,
            'number_list': list(number_list),
            'events': events,
            'user': user,
            '_id': _id,
            'turn_chosen': turn_chosen,
            'number_rolled': number_rolled,
            'now': current_date,
            'date_will_random': date,
            'time_random': RAMDOM_HOUR,
            'random_before': DATE_RANDOM
        })
        # Logging data
        message_logger.info(f"{user['username']} vào trang chọn số.")
        return render_template(
            'choose_number/choose_number.html',
            title="Chọn số",
            data=data
        )


def insert_select_number(str_number_list, user, event, user_event, max_range):
    number_list = specific_number_list(max_range, event['limit_repeat'], event['_id'], user['_id'])
    number_list = number_list.get('pickable_numbers')
    # logger.info(f"Original list: {number_list}")
    # Get the list and use set to remove duplicates values
    list_selected = set(str_number_list.split(', '))
    list_selected = list(list_selected)
    invalid_number = []
    user_was_selected = []
    if 'selected_number' in user_event:
        user_was_selected = user_event['selected_number'].split(', ')
    # Validate if number selected more than turn choices
    if len(list_selected) > int(user_event['turn_roll']):
        return {
            'message': f"Bạn chỉ được chọn {user_event['turn_roll']} số.",
            'status': 'warning',
            'number_selected': user_was_selected
        }
    # Sorting data number selected
    if len(list_selected) == 1 and list_selected[0] == '':
        id_roll = str(user_event['_id'])
        form_data = {"$unset": {"selected_number": "", "number_choices": ""}}
        try:
            USER_JOIN_EVENT.update_one({"_id": ObjectId(id_roll)}, form_data)
            logger.info("Very ok")
        except Exception as e:
            error = traceback.format_exc()
            logger.info(f"Error {e} | Details: {error}")
        logger.info("Loại bỏ số")
        return {
            'message': f"Loại bỏ tất cả các số.",
            'status': 'success',
            'number_selected': [user_was_selected]
        }

    list_selected = sorted(list_selected, key=int)
    if int(list_selected[len(list_selected) - 1]) > max_range:
        return {
            'message': f"Lựa chọn không hợp lệ, vui lòng chọn lại.",
            'status': 'warning',
            'number_selected': user_was_selected
        }
    check_list_selected = list(map(int, list_selected))
    user_was_selected = list(map(int, user_was_selected))
    logger.info(user_was_selected)
    number_list = number_list + user_was_selected
    logger.info(f"List of number {number_list}")
    for i in check_list_selected:
        logger.info(f"Type of i: {type(i)} | type of compare: {type(number_list)}")
        if i not in number_list:
            invalid_number.append(i)
        else:
            continue
    logger.info(f"invalid number {invalid_number}")
    if any(invalid_number):
        return {
            'message': f"Các số {invalid_number} đã được chọn.",
            'status': 'warning',
            'number_selected': user_was_selected
        }
    # Change data type of close_date value to datetime
    close_date = event['date_close']
    # Validate if current date > closure date
    if not event['is_active']:
        return {
            'message': f"Sự kiện được tạm dừng hoặc đã kết thúc.",
            'status': 'warning'
        }
    if datetime.now().strftime("%Y-%m-%d") > close_date:
        return {
            'message': f"Sự kiện đã kết thúc vào ngày {event['date_close']}.",
            'status': 'warning'
        }
    # Get data from form
    form_data = {
        'selected_number': ', '.join(list_selected),
        'number_choices': len(list_selected),
        'date_created': datetime.utcnow()
    }
    # Case first time choose number
    if 'selected_number' not in user_event and 'number_choices' not in user_event:
        # Try handle add new rolled number and number choices
        try:
            id_roll = str(user_event['_id'])
            join_event_model.update(ObjectId(id_roll), form_data)
            message_logger.info(
                f"Sự kiện: {event['event_name']}: User '{user['username']}' đã chọn [{form_data['number_choices']}] số [{form_data['selected_number']}].")
            return {
                'message': f"Chọn các số [{form_data['selected_number']}] cho sự kiện '{event['event_name'].upper()}' thành công.",
                'status': 'success',
                'number_selected': list_selected
            }
        # Return message with error
        except Exception as e:
            logger.error(f"Error when choosing number.\n{e}")
            return {
                'message': "Lỗi server, vui lòng thử lại.",
                'status': 'warning',
                'number_selected': user_was_selected
            }
    # Case re-choice number
    else:
        # Try handle update and replace old numbers
        try:
            form_data.pop('date_created')
            form_data.update({'date_updated': datetime.utcnow()})
            id_roll = str(user_event['_id'])
            join_event_model.update(ObjectId(id_roll), form_data)
            message_logger.info(
                f"Sự kiện: {event['event_name']}: User '{user['username'].upper()}' đã cập nhật chọn [{form_data['number_choices']}] số [{form_data['selected_number']}].")
            return {
                'message': f"Chọn các số [{form_data['selected_number']}] cho sự kiện '{event['event_name'].upper()}' thành công.",
                'status': 'success',
                'number_selected': list_selected
            }
        # Return exception error
        except Exception as e:
            error_info = traceback.format_exc()
            logger.error(f"Error when re choosing number.\n{e} | Error: {error_info}")
            return {
                'message': "Lỗi server, vui lòng thử lại.",
                'status': 'warning',
                'number_selected': user_was_selected
            }


@app.route('/thong-tin')
def information():
    # authorize user
    user = authorize_user()
    if not user:
        flash(Markup(
            f'Bạn phải đăng nhập để xem thông tin sự kiện. <strong><a href="{url_for("user.login")}" style="color: '
            f'#3a47a6">Click để đăng nhập</a></strong>'),
            'warning')
        return redirect(url_for('home'))
    # Create data dict to store data
    data = {}

    list_event_joined = list()
    # Get event user joined
    join_event = join_event_model.get_many({'user_id': user['_id']})
    for event in join_event:
        list_event_joined.append(event['event_id'])
        logger.info(f"Event join: {event}")
        # If user was selected number
        if 'selected_number' in event and 'number_choices' in event:
            data[event['event_id']] = {
                'turn_roll': int(event['turn_roll']),
                'number_choices': int(event['number_choices']),
                'selected_number': ', '.join(sorted(event['selected_number'].split(', '), key=int)),
                'user_point': event['user_point']
            }
        # When user was not selected number
        else:
            data[event['event_id']] = {
                'turn_roll': int(event['turn_roll']),
                'number_choices': 0,
                'selected_number': '',
                'user_point': event['user_point']
            }
    # Get event user was joined
    for id_event in list_event_joined:
        event = event_model.get_one(ObjectId(id_event))
        data[id_event].update({
            'event_name': event['event_name'],
            'date_close': event['date_close'],
            'event_active': event['is_active'],
            'point_exchange': event['point_exchange']
        })
    logger.info(f'Data: {data}')
    # Return render template and log info
    message_logger.info(f"User {user['username']} tiến vào trang thông tin")
    return render_template('choose_number/info.html', infos=data, user=user, title="Thông tin sự kiện")


@app.route('/thong-tin/prints/<string:_id>')
def print_info(_id):
    # Authorize user
    user = authorize_user()
    if not user:
        flash(Markup(
            f'Bạn phải đăng nhập để in thông tin. <strong><a href="{url_for("user.login")}" style="color: '
            f'#3a47a6">Click để đăng nhập</a></strong>'),
            'warning')
        return redirect(url_for('home'))
    # Get current event to choose number
    events = event_model.get_one({'_id': ObjectId(_id)})
    # Get turn of choice number
    user_joins = join_event_model.get_one({'user_id': user['_id'], 'event_id': _id})
    # Assign turn choice for user
    rolled = join_event_model.get_one({'user_id': user['_id'], 'event_id': _id})
    # Get data from user joined event
    if 'selected_number' in rolled and 'number_choices' in rolled:
        # Get list of selected number
        number_rolled = rolled['selected_number'].split(', ')
        turn_chosen = len(number_rolled)
        # Data to print
        print_data = {
            'event_name': events['event_name'],
            'username': user['username'],
            'usercode': user['usercode'],
            'user_point': rolled['user_point'],
            'point_exchange': events['point_exchange'],
            'turn_roll': user_joins['turn_roll'],
            'turn_chosen': turn_chosen,
            'number_rolled_str': rolled['selected_number']
        }
        # HTML template
        template = render_template(
            'template/pdf_output.html',
            data=print_data,
            number_rolled=number_rolled,
            title="In file"
        )
        filename = f"Dongxanh-{events['event_name']}-{user['username']}.pdf"
        # Return template pdf
        message_logger.info(f"User {user['username']} đã in sự kiện {events['event_name']}.")
        return render_pdf(HTML(string=template))
    else:
        return redirect(url_for('information'))


@app.route('/api/number_list/<string:event_id>', methods=['GET'])
def get_number_list(event_id):
    user = authorize_user()
    if not user:
        return jsonify({'message': 'Cần đăng nhập để lấy thông tin.'})
    event = event_model.get_one({'_id': ObjectId(event_id)})
    if not event:
        return jsonify({'message': 'Không thấy sự kiện'})
    max_range = event.get('range_number', MAX_NUMBER)
    num_data = specific_number_list(max_range, event.get('limit_repeat'), event_id, user['_id'])
    return jsonify({
        "message": "Lấy tất cả tem thành công.",
        "data": num_data
    })


def specific_number_list(max_range: int, limit: int, event_id: str, user_id: str):
    list_selected, all_number_selected, user_selected = [], [], []
    unavailable_number = {}
    # user_rolled check which number chosen by user
    user_rolled = join_event_model.get_one({'event_id': event_id, 'user_id': user_id})
    if user_rolled is None:
        return jsonify({
            "message": "Unauthorized, not join event."
        })
    if 'selected_number' in user_rolled and 'number_choices' in user_rolled:
        number_selected = user_rolled['selected_number'].split(', ')
        for number in number_selected:
            try:
                user_selected.append(int(number))
            except ValueError:
                continue
    logger.info(f"Number user selected: {user_selected}")
    # rolled get all number was chosen
    rolled = join_event_model.get_all()
    if rolled:
        for roll in rolled:
            if 'selected_number' in roll and 'number_choices' in roll and roll['event_id'] == event_id:
                if roll['selected_number'] != '':
                    list_selected.append(roll['selected_number'])
    # Add number was selected to list selected
    for number in list_selected:
        arr = number.split(', ')
        for i in arr:
            all_number_selected.append(int(i))
    # Dict for number selected
    for num in all_number_selected:
        if num not in unavailable_number:
            unavailable_number[num] = 1
        else:
            # Counting up for number selected
            unavailable_number[num] += 1
        # When number selected own by user, remove 1 count from unavailable dict
        if num in user_selected:
            unavailable_number[num] -= 1
    list_number = {}
    for i in range(1, max_range + 1):
        if i > 0:
            if i in unavailable_number:
                if limit - unavailable_number[i] > 0 and unavailable_number[i] > 0:
                    list_number[i] = limit - unavailable_number[i]
            else:
                list_number[i] = limit
        # logger.info(f"List avaiable number: {list_number}")
    pickable_numbers = list(list_number.keys())
    return {
        "pickable_numbers": pickable_numbers,
        "user_selected": user_selected,
        "rest_number": (max_range * limit) - len(all_number_selected)
    }

from bson import ObjectId
from flask import render_template, request, redirect, url_for, flash
from _datetime import datetime, timedelta

from flask_weasyprint import render_pdf, HTML
from markupsafe import Markup

from src.forms import NumberSelectedForm
from src.app import app
from src.logs import message_logger, logger
from src.requests.authenticate import authorize_user
from src.utils.constants import event_model, join_event_model, user_model, MAX_NUMBER_RANGE_DEFAULT as MAX_NUMBER
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


@app.route('/quay-so/<string:_id>', methods=['POST', 'GET'])
def roll_number(_id):
    # authorize user
    user = authorize_user()
    if not user:
        flash(Markup(
            f'Bạn phải đăng nhập để quay số. <strong><a href="{url_for("user.login")}" style="color: '
            f'#3a47a6">Click để đăng nhập</a></strong>'),
            'warning')
        return redirect(url_for('home'))
    # Get current event to choose number
    events = event_model.get_one({'_id': ObjectId(_id)})
    # Edit element of event
    events['_id'] = str(events['_id'])
    events.pop('date_created')
    max_range = MAX_NUMBER if 'range_number' not in events else events['range_number']
    # Format date follow by day-month-year for easily readable
    date_show = datetime.strptime(events['date_close'], '%Y-%m-%d').strftime('%d-%m-%Y')
    events.update({'date_show': date_show})
    logger.debug(events['date_close'])
    # Get data rolled if user has joined event
    rolled = join_event_model.get_one({'user_id': user['_id'], 'event_id': _id})
    # Assign turn choice for user
    user['turn_roll'] = rolled['turn_roll']
    user['point'] = rolled['user_point']
    turn_chosen = 0
    number_rolled = []
    if 'selected_number' in rolled and 'number_choices' in rolled:
        number_rolled = rolled['selected_number'].split(', ')
        if 'number_choices' not in rolled:
            rolled['number_choices'] = len(number_rolled)
        turn_chosen = rolled['number_choices']
    # Get the form data
    form = NumberSelectedForm()
    # Post method
    if request.method == 'POST':
        # Get the list and use set to remove duplicates values
        list_selected = set(form.number.data.split(', '))
        list_selected = list(list_selected)
        # Validate if number selected more than turn choices
        if len(list_selected) > int(user['turn_roll']):
            flash(f"Bạn chỉ được chọn {user['turn_roll']} số.", 'warning')
            return redirect(url_for('roll_number', _id=_id))
        # Sorting data number selected
        list_selected = sorted(list_selected, key=int)
        if list_selected[len(list_selected) - 1] > max_range:
            flash(f"Lựa chọn không hợp lệ, vui lòng chọn lại.", 'warning')
            return redirect(url_for('roll_number', _id=_id))
        # Change data type of close_date value to datetime
        close_date = events['date_close']

        # Validate if current date > closure date
        if not events['is_active']:
            flash(f"Sự kiện được tạm dừng hoặc đã kết thúc.", 'warning')
            return redirect(url_for('choose_event'))
        if datetime.now().strftime("%Y-%m-%d") > close_date:
            flash(f"Sự kiện đã kết thúc 23h59 phút ngày {events['date_close']}.", 'warning')
            return redirect(url_for('choose_event'))
        # Get data from form
        form_data = {
            'selected_number': ', '.join(list_selected),
            'number_choices': len(list_selected),
            'date_created': datetime.utcnow()
        }
        # Case first time choose number
        if 'selected_number' not in rolled and 'number_choices' not in rolled:
            try:
                id_roll = str(rolled['_id'])
                join_event_model.update(ObjectId(id_roll), form_data)
                flash(
                    f"Chọn các số [{form_data['selected_number']}] cho sự kiện '{events['event_name'].upper()}' thành công.",
                    "success")
                message_logger.info(
                    f"Sự kiện: {events['event_name']}: User '{user['username']}' đã chọn [{form_data['number_choices']}] số [{form_data['selected_number']}].")
                return redirect(url_for('roll_number', _id=_id))
            except Exception as e:
                flash("Lỗi server, vui lòng thử lại.")
                logger.error(f"Error when choosing number.\n{e}")
                return redirect(url_for('choose_event'))
        # Case re-choice number
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
                    f"Sự kiện: {events['event_name']}: User '{user['username'].upper()}' đã cập nhật chọn [{form_data['number_choices']}] số [{form_data['selected_number']}].")
                return redirect(url_for('roll_number', _id=_id))
            except Exception as e:
                flash("Lỗi server, vui lòng thử lại.")
                logger.error(f"Error when re choosing number.\n{e}")
                return redirect(url_for('choose_event'))
    else:
        # Create a number list for user can choose
        number_list = create_number_list(max_range, events['limit_repeat'], _id, user['_id'])
        # Get current page for compare
        current_date = datetime.now().strftime('%Y-%m-%d')
        date_close = datetime.strptime(events['date_close'], "%Y-%m-%d")
        # Date random to take random if user didn't select number
        date_random = date_close - timedelta(days=3)
        date = date_random.strftime('%d-%m-%Y')
        # Logging data
        message_logger.info(f"{user['username']} vào trang chọn số.")
        return render_template(
            'choose_number/choose_number.html',
            number_list=number_list, title="Chọn số",
            form=form,
            events=events,
            user=user,
            _id=_id,
            turn_chosen=turn_chosen,
            number_rolled=number_rolled,
            now=current_date,
            date_will_random=date
        )


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
    data = {}
    list_event_joined = list()

    join_event = join_event_model.get_many({'user_id': user['_id']})
    for event in join_event:
        list_event_joined.append(event['event_id'])
        if 'selected_number' in event and 'number_choices' in event:
            data[event['event_id']] = {
                'turn_roll': int(event['turn_roll']),
                'number_choices': int(event['number_choices']),
                'selected_number': ', '.join(sorted(event['selected_number'].split(', '), key=int)),
                'user_point': event['user_point']
            }
        else:
            data[event['event_id']] = {
                'turn_roll': int(event['turn_roll']),
                'number_choices': 0,
                'selected_number': '',
                'user_point': event['user_point']
            }
    for id_event in list_event_joined:
        event = event_model.get_one(ObjectId(id_event))
        data[id_event].update({
            'event_name': event['event_name'],
            'date_close': event['date_close'],
            'event_active': event['is_active'],
            'point_exchange': event['point_exchange']
        })
    message_logger.info(f"User {user['username']} tiến vào trang thông tin")
    return render_template('choose_number/info.html', infos=data, user=user, title="Thông tin sự kiện")


@app.route('/thong-tin/prints/<string:_id>')
def print_info(_id):
    # authorize user
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
    if 'selected_number' in rolled and 'number_choices' in rolled:
        number_rolled = rolled['selected_number'].split(', ')
        turn_chosen = len(number_rolled)
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
        template = render_template(
            'template/pdf_output.html',
            data=print_data,
            number_rolled=number_rolled,
            title="In file"
        )
        filename = f"Dongxanh-{events['event_name']}-{user['username']}.pdf"
        # return template
        message_logger.info(f"User {user['username']} đã in sự kiện {events['event_name']}.")
        return render_pdf(HTML(string=template))
    else:
        return redirect(url_for('information'))

import traceback
import pandas as pd

from io import BytesIO
from _datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file

from src.forms import EventForm
from src.app import logger
from src.requests.authenticate import admin_authorize
from src.requests.roll_number import insert_select_number
from src.utils.constants import event_model, join_event_model, user_model, MAX_NUMBER_RANGE_DEFAULT as MAX_NUMBER
from src.utils.utilities import update_user_join, create_folder, handle_random_for_each_user, create_number_list

events = Blueprint('event', __name__)


@events.route('/')
def index():
    # Authorize is admin
    is_admin = admin_authorize()
    if not is_admin:
        flash("Bạn không được phép truy cập vào trang này.", 'danger')
        return redirect(url_for('home'))
    # Get all data events
    data = event_model.get_all()
    data_list = list(data)
    # Format date data for each event
    for event in data_list:
        try:
            event['date_close'] = event['date_close'].strftime('%Y-%m-%d')
        except AttributeError:
            event['date_close'] = event['date_close']
    return render_template('admin/events/index.html', events=data_list, title="Quản lý sự kiện")


@events.route('/create', methods=['POST', 'GET'])
def insert():
    # Authorize is admin
    is_admin = admin_authorize()
    if not is_admin:
        flash("Bạn không được phép truy cập vào trang này.", 'danger')
        return redirect(url_for('home'))
    # Get form rule
    form = EventForm()
    # Get current datetime for checking status in template
    now = datetime.now().strftime('%Y-%m-%d')
    if request.method == 'POST':
        # Get current datetime when updating
        current_time = datetime.now()
        # Format datetime now compare with date close
        current_date = current_time.strftime('%Y-%m-%d')
        close_date = form.date_close.data.strftime('%Y-%m-%d')
        # Status will activate when date close smaller than current date
        is_active = False if current_date > close_date else True
        # Create data dict
        data_form = {
            'event_name': form.name.data,
            'limit_repeat': abs(int(form.repeat_limit.data)),
            'point_exchange': abs(int(form.point_exchange.data)),
            'range_number': abs(int(form.range_number.data)),
            'date_start': form.date_start.data.strftime('%Y-%m-%d'),
            'date_close': form.date_close.data.strftime('%Y-%m-%d'),
            'is_active': is_active,
            'date_created': current_time
        }
        # Validate form data
        if form.validate_on_submit():
            # Process data to database
            try:
                event_model.create(data_form)
                flash(f'Tạo thành công "{data_form["event_name"]}".', 'success')
                return redirect(url_for('event.index'))
            # Except error
            except Exception as e:
                error_info = traceback.format_exc()
                logger.error(f'Error creating event.\nError: {e}\n{error_info}"')
                flash('Server gặp sự cố, vui lòng thử lại sau.', 'warning')
        flash('Tạo tài khoản thất bại, vui lòng kiểm tra lại thông tin.', 'warning')
        return redirect(url_for('event.index'))
    return render_template('admin/events/create.html', form=form, date_now=now, title="Thêm sự kiện")


@events.route('edit/<string:_id>', methods=['POST', 'GET'])
def update(_id):
    # Authorize is admin
    is_admin = admin_authorize()
    if not is_admin:
        flash("Bạn không được phép truy cập vào trang này.", 'danger')
        return redirect(url_for('home'))
    # Get specific event for updating
    spec_event = event_model.get_one({'_id': ObjectId(_id)})
    # Try to change datetime format
    try:
        spec_event['date_close'] = spec_event['date_close'].strftime('%Y-%m-%d')
    except AttributeError:
        spec_event['date_close'] = spec_event['date_close']
    # Get form field and data
    form = EventForm()
    # If specific event existed
    if spec_event:
        if request.method == 'POST':
            # Get current datetime format to compare with date close
            current_date = datetime.now().strftime('%Y-%m-%d')
            form_date = form.date_close.data.strftime('%Y-%m-%d')
            # Status will activate when date close smaller than current date
            is_active = False if current_date > form_date else form.is_active.data
            # Create data dict
            data_form = {
                'event_name': form.name.data,
                'limit_repeat': abs(int(form.repeat_limit.data)),
                'point_exchange': abs(int(form.point_exchange.data)),
                'range_number': abs(int(form.range_number.data)),
                'date_close': form_date,
                'is_active': is_active,
                'date_updated': datetime.utcnow()
            }
            # Validate form fields
            if form.validate_on_submit():
                # Try updating data to database
                try:
                    event_model.update(ObjectId(_id), data_form)
                    update_user_join(_id)
                    flash(f'Cập nhật thành công "{data_form["event_name"]}".', 'success')
                    return redirect(url_for('event.index'))
                # Except error
                except Exception as e:
                    error_info = traceback.format_exc()
                    logger.error(f'Error updating event.\nError: {e}\n{error_info}"')
            flash(f'Cập nhật thất bại, vui lòng kiểm tra lại.', 'danger')
            return redirect(url_for('event.update', _id=_id))
        # Return GET method
        return render_template('admin/events/edit.html', form=form, event=spec_event, title="Sửa sự kiện")
    # Return event index when _id not found
    logger.info(f"Cannot find event id: {_id}")
    flash(f'Không tìm thấy sự kiện.', 'warning')
    return redirect(url_for('event.index'))


@events.route('event-detail/<string:_id>', methods=['GET'])
def event_detail(_id):
    context = {}
    # Authorize is admin
    adm = admin_authorize()
    if not adm:
        flash("Bạn không được phép truy cập vào trang này.", 'danger')
        return redirect(url_for('home'))
    # Get search query
    s_query = request.args.get('search_account', type=str)
    # Pagination settings
    perpage = 10
    # Get current page for specific data
    current_page = request.args.get('page', 1, type=int)
    # Get current event to get name and point exchange
    current_event = event_model.get_one({'_id': ObjectId(_id)})
    point_exchange = current_event.get('point_exchange', None)
    # Get all user was joined event
    events_joined = join_event_model.get_many({'event_id': _id})
    # List user id
    user_id_list = list()
    # List all user was joined event
    for event in events_joined:
        # Get user id
        user_id = ObjectId(event['user_id'])
        user_id_list.append(user_id)
    if s_query:
        # Try making query to ObjectId to check if it was id
        try:
            query_data = {
                '_id': ObjectId(s_query)
            }
        # Get query data from query search
        except InvalidId:
            query_data = {
                '$or': [
                    {'username': {'$regex': s_query, "$options": "i"}},
                    {'usercode': {'$regex': s_query, "$options": "i"}},
                ]
            }
    else:
        # Default query data
        query_data = {
            '_id': {'$ne': ObjectId(adm['_id']), '$in': user_id_list}
        }
    # Process pagination
    user_list, max_page = user_model.pagination(current_page, perpage, query_data)
    # Loop through user to add more info
    user_data = loop_through_user(user_list, _id, point_exchange)
    # Put all require render data to context
    context['user_list'] = user_data
    context['event_name'] = current_event['event_name']
    context['max_page'] = max_page
    context['current_page'] = current_page
    context['s_query'] = s_query
    context['_id'] = _id
    return render_template('admin/events/event_joins.html', context=context)


def loop_through_user(user_list, _id, point_exchange):
    for user in user_list:
        # Get join events to get info user join events
        event = join_event_model.get_one({'event_id': _id, 'user_id': str(user['_id'])})
        # Get user_point and turn_roll
        user_point = event['user_point']
        turn_roll = event['turn_roll']
        rest_point = user_point - (turn_roll * point_exchange)
        user.update({
            'user_point': user_point,
            'turn_roll': turn_roll,
            'rest_point': rest_point
        })
        # If user joined then get selected number and number choices
        if 'selected_number' in event and 'number_choices' in event:
            number_choices = event['number_choices']
            rest_choices = turn_roll - number_choices
            user.update({
                'selected_number': event['selected_number'],
                'number_choices': number_choices,
                'rest_choices': rest_choices
            })
    return user_list


# def saveFile():
# file_doc = request.files.get('desc_file')
# file_image = request.files.get('desc_image')
# event_folder = create_folder(data_form['event_name'])
# doc_name = secure_filename(file_doc.filename)
# img_name = secure_filename(file_image.filename)
# file_doc.save(os.path.join(event_folder, doc_name))
# file_image.save(os.path.join(event_folder, img_name))
# data_form.update({
#     'file_pdf_doc': doc_name,
#     'file_image_doc': img_name
# })


@events.route('/event-print-user/<_id>')
def print_events_joins_data(_id):
    # Get event names
    event_names = event_model.get_one({'_id': ObjectId(_id)}).get('event_name')
    filename = event_names.split(' ')
    # Restructure filename
    filename = '-'.join(filename) + '.xlsx'
    # Create data frame from data
    df_data = create_dataframe(_id)
    # Create output stream and ExcelWriter
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    # Write DataFrame into ExcelWriter
    df_data.to_excel(writer, startrow=0, merge_cells=False, sheet_name="Sheet_1", index=False, header=False)
    workbook = writer.book
    worksheet = writer.sheets["Sheet_1"]
    worksheet.set_column(2, 2, 20)
    worksheet.set_column(3, 3, 60)
    # Close writer data to excel
    writer.close()
    # Return to pointer which has all data of xlsx
    output.seek(0)
    # Return and download file
    return send_file(output, download_name=filename, as_attachment=True)


def create_dataframe(_id):
    # Create first row title
    title_row = ['Mã KH', 'Đã chọn', 'Tên KH', 'Địa chỉ']
    # Append first row to data list
    data = [title_row]
    # Get all user id were joined event
    events_joined = join_event_model.get_many({'event_id': _id})
    # Create list save all user_id
    user_id_list = list()
    # List all user was joined event
    for event in events_joined:
        # Get user id
        user_id = ObjectId(event['user_id'])
        user_id_list.append(user_id)
    # Get list of user from list user_id
    user_list = list(user_model.get_many({'_id': {'$in': user_id_list}}))
    # Loop through user list to get data for print
    for idx, user in enumerate(user_list):
        # Get join events to get info user join events
        event = join_event_model.get_one({'event_id': _id, 'user_id': str(user['_id'])})
        # If user joined then get selected number and loop through for columns data
        selected_number = event.get('selected_number', None)
        address = user.get('address', '')
        if address == '':
            address = user.get('area_detail', '') + ', ' + user.get('area', '')
        if selected_number is not None:
            selected_number_list = map(int, selected_number.split(', '))
            for indx, number in enumerate(selected_number_list):
                # Create row data list for input data to each row
                row_data = [user['usercode'], number, user.get('fullname', ''), address]
                data.append(row_data)
    # Create data frame from data list
    df = pd.DataFrame(data)
    return df


@events.route('/user-join-event/details/<event_id>||<user_id>')
def user_join_event_detail(event_id, user_id):
    # Authorize is admin
    is_admin = admin_authorize()
    if not is_admin:
        flash("Bạn không được phép truy cập vào trang này.", 'danger')
        return redirect(url_for('home'))
    # Create context for send data to template
    context = {}
    # Get data event, user, user_event and string their _id
    event = event_model.get_one({'_id': ObjectId(event_id)})
    user = user_model.get_one({'_id': ObjectId(user_id)})
    user_event = join_event_model.get_one({'event_id': event_id, 'user_id': user_id})
    event['_id'] = str(event['_id'])
    user['_id'] = str(user['_id'])
    user_event['_id'] = str(user_event['_id'])
    # Get range of number
    max_range = event.get('range_number', MAX_NUMBER)
    # Create list avaiable number
    number_list = list(create_number_list(max_range, event.get('limit_repeat', 1), event_id, user_id))
    context.update({'event': event, 'user': user, 'user_event': user_event, 'number_list': number_list})
    return render_template('admin/events/user_join_event.html', context=context)


@events.route('/user-join-event/details/<event_id>||<user_id>/select', methods=['POST'])
def select_number(event_id, user_id):
    # Authorize is admin
    is_admin = admin_authorize()
    if not is_admin:
        flash("Bạn không được phép truy cập vào trang này.", 'danger')
        return redirect(url_for('home'))
    # Get data event, user, user_event and string their _id
    event = event_model.get_one({'_id': ObjectId(event_id)})
    user = user_model.get_one({'_id': ObjectId(user_id)})
    user_event = join_event_model.get_one({'event_id': event_id, 'user_id': user_id})
    event['_id'] = str(event['_id'])
    user['_id'] = str(user['_id'])
    user_event['_id'] = str(user_event['_id'])
    str_number_list = request.json.get('str_number_list')
    max_range = event.get('range_number', MAX_NUMBER)
    logger.info('test this: ' + str_number_list)
    data = insert_select_number(str_number_list, user, event, user_event, max_range)
    return jsonify({
        'message': 'Select number successful',
        'data': data
    })

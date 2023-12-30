from _datetime import datetime
from bson import ObjectId
from flask import Blueprint, render_template, request, redirect, url_for, flash

from src.forms import EventForm
from src.logs import logger
from src.models import Models
from src.mongodb import EVENT_TABLE, USER_JOIN_EVENT
from src.requests.authenticate import admin_authorize

import traceback

events = Blueprint('event', __name__)
event_model = Models(table=EVENT_TABLE)
join_event_model = Models(table=USER_JOIN_EVENT)


@events.route('/')
def index():
    # Authorize is admin
    is_admin = admin_authorize()
    if not is_admin:
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
        form_date = form.date_close.data.strftime('%Y-%m-%d')
        # Status will activate when date close smaller than current date
        is_active = False if current_date > form_date else True
        # Create data dict
        data_form = {
            'event_name': form.name.data,
            'limit_repeat': abs(int(form.repeat_limit.data)),
            'point_exchange': abs(int(form.point_exchange.data)),
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
                'date_close': form_date,
                'is_active': is_active,
                'date_created': datetime.utcnow()
            }
            # Validate form fields
            if form.validate_on_submit():
                # Try updating data to database
                try:
                    event_model.update(ObjectId(_id), data_form)
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


@events.route('event/detail/<string:_id>', methods=['GET'])
def event_detail(_id, event_name):
    # Authorize is admin
    is_admin = admin_authorize()
    if not is_admin:
        return redirect(url_for('home'))
    event_joined = join_event_model.get_many({'event_id': _id})
    return render_template('admin/events/event_joins.html')


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

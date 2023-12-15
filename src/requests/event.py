import os
from _datetime import datetime

from bson import ObjectId
from flask import Blueprint, render_template, request, redirect, url_for, flash

from src.app import create_folder
from src.forms import EventForm
from src.models import Models
from src.mongodb import EVENT_TABLE, USER_JOIN_EVENT
from src.requests.authenticate import admin_authorize, authorize_user
from werkzeug.utils import secure_filename


events = Blueprint('event', __name__)
event_model = Models(table=EVENT_TABLE)
join_event_model = Models(table=USER_JOIN_EVENT)


@events.route('/')
def index():
    is_admin = admin_authorize()
    if not is_admin:
        return redirect(url_for('home'))
    data = event_model.get_all()
    data_list = list(data)
    create_folder("test1234")
    for event in data_list:
        try:
            event['date_close'] = event['date_close'].strftime('%Y-%m-%d')
        except AttributeError:
            event['date_close'] = event['date_close']
    return render_template('events/index.html', events=data_list)


@events.route('/create', methods=['POST', 'GET'])
def insert():
    is_admin = admin_authorize()
    if not is_admin:
        return redirect(url_for('home'))
    form = EventForm()
    if request.method == 'GET':
        now = datetime.now().strftime('%Y-%m-%d')
        return render_template('events/create.html', form=form, date_now=now)
    if request.method == 'POST':
        file_doc = request.files.get('desc_file')
        file_image = request.files.get('desc_image')
        data_form = {
            'event_name': form.name.data,
            'limit_repeat': int(form.repeat_limit.data),
            'date_close': form.date_close.data.strftime('%Y-%m-%d'),
            'is_active': True,
            'date_created': datetime.utcnow()
        }
        if form.validate_on_submit():
            try:
                event_folder = create_folder(data_form['event_name'])
                doc_name = secure_filename(file_doc.filename)
                img_name = secure_filename(file_image.filename)
                file_doc.save(os.path.join(event_folder, doc_name))
                file_image.save(os.path.join(event_folder, img_name))
                data_form.update({
                    'file_pdf_doc': doc_name,
                    'file_image_doc': img_name
                })
                event_model.create(data_form)
                flash(f'Tạo thành công "{data_form["event_name"]}".', 'success')
                return redirect(url_for('event.index'))
            except Exception as e:
                print("Error.", e)
                flash('Server gặp sự cố, vui lòng thử lại sau.', 'warning')
                return redirect(url_for('event.index'))
        return redirect(url_for('home'))


@events.route('edit/<string:_id>', methods=['POST', 'GET'])
def update(_id):
    is_admin = admin_authorize()
    if not is_admin:
        return redirect(url_for('home'))
    spec_event = event_model.get_one({'_id': ObjectId(_id)})
    try:
        spec_event['date_close'] = spec_event['date_close'].strftime('%Y-%m-%d')
    except AttributeError:
        spec_event['date_close'] = spec_event['date_close']
    form = EventForm()
    if spec_event:
        if request.method == 'GET':
            return render_template('events/edit.html', form=form, event=spec_event)
        elif request.method == 'POST':
            data_form = {
                'event_name': form.name.data,
                'limit_repeat': form.repeat_limit.data,
                'date_close': form.date_close.data.strftime('%Y-%m-%d'),
                'is_active': form.is_active.data,
                'date_created': datetime.utcnow()
            }
            if form.validate_on_submit():
                try:
                    event_model.update(ObjectId(_id), data_form)
                    flash(f'Cập nhật thành công "{data_form["event_name"]}".', 'success')
                    return redirect(url_for('event.index'))
                except Exception as e:
                    print("Error updating event. ", e)
            flash(f'Cập nhật thất bại, vui lòng kiểm tra lại.', 'danger')
            return render_template('events/edit.html', form=form, event=spec_event)
    flash(f'Không tìm thấy sự kiện.', 'warning')
    return redirect(url_for('event.index'))

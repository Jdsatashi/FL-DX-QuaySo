from _datetime import datetime

from bson import ObjectId
from flask import Blueprint, render_template, request, redirect, url_for, flash

from src.forms import EventForm
from src.models import Models
from src.mongodb import EVENT_TABLE, USER_JOIN_EVENT
from src.requests.authenticate import admin_authorize, authorize_user


events = Blueprint('event', __name__)
event_model = Models(table=EVENT_TABLE)


@events.route('/')
def index():
    data = event_model.get_many()
    # for event in data:
    #     event['_id'] = str(event['_id'])
    return render_template('events/index.html', events=data)


@events.route('/create', methods=['POST', 'GET'])
def insert():
    is_admin = admin_authorize()
    form = EventForm()
    if not is_admin:
        return redirect(url_for('home'))
    if request.method == 'GET':
        return render_template('events/create.html', form=form)
    if request.method == 'POST':
        data_form = {
            'event_name': form.name.data,
            'limit_repeat': form.repeat_limit.data,
            'date_close': datetime.combine(form.date_close.data, datetime.min.time()),
            'date_created': datetime.utcnow()
        }
        if form.validate_on_submit():
            try:
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
    spec_event['date_close'] = spec_event['date_close'].strftime('%m-%d-%Y')
    # spec_event['date_close'] = datetime.strptime(spec_event['date_close'], '%Y-%m-%d')
    form = EventForm()
    if spec_event:
        if request.method == 'GET':
            return render_template('events/edit.html', form=form, event=spec_event)
        elif request.method == 'POST':
            data_form = {
                'event_name': form.name.data,
                'limit_repeat': form.repeat_limit.data,
                'date_close': datetime.combine(form.date_close.data, datetime.min.time()),
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

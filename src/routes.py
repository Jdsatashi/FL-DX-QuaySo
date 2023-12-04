from flask import render_template, session

from src import app
from .requests.authenticate import authorize_user


@app.route('/')
def home():
    user = authorize_user()
    if 'username' in session or user:
        if '_id' in session:
            session['_id'] = str(user['_id'])
    return render_template('home.html', title='Home page')


from .requests import authenticate, roll_number, administrator
auth_route = authenticate
roll_number_route = roll_number
admin_route = administrator

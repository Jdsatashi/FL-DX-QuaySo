from flask import render_template, session, redirect, url_for

from src import app
from .mongodb import ACCOUNT_TABLE
from .requests.authenticate import authorize_user


@app.route('/')
def home():
    user = authorize_user()
    if not user:
        return render_template('home.html', title='Home page')
    elif session['username']:
        user = ACCOUNT_TABLE.find_one({
            'username': session['username']
        })
        if '_id' in session:
            session['_id'] = str(user['_id'])
    return render_template('home.html', title='Home page')


from .requests import authenticate, roll_number, administrator
auth_route = authenticate
roll_number_route = roll_number
admin_route = administrator

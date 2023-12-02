from flask import render_template

from src import app


@app.route('/')
def home():
    return render_template('home.html', title='Home page')


from .requests import authenticate, roll_number, administrator
auth_route = authenticate
roll_number_route = roll_number
admin_route = administrator

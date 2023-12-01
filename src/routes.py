from flask import render_template

from src import app


@app.route('/')
def home():
    return render_template('home.html', title='Home page')


from .requests import authenticate, roll_number
auth_route = authenticate
roll_number = roll_number

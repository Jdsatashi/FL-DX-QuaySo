from flask import render_template, session

from src.app import app
from src.requests.authenticate import authorize_user


# function to home page
@app.route('/')
def home():
    user = authorize_user()
    if 'username' in session or user:
        if '_id' in session:
            session['_id'] = str(user['_id'])
    return render_template('home.html', title='Home page')


# function handle error 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/error.html', error_code=404, error_message=str(e)), 404


# function handle error 400
@app.errorhandler(400)
def bad_request(e):
    return render_template('errors/error.html', error_code=400, error_message=str(e)), 400


# function handle error 403
@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/error.html', error_code=403, error_message=str(e)), 403


# function handle error 500
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/error.html', error_code=500, error_message=str(e)), 500


# function handle error 503
@app.errorhandler(503)
def service_unavailable(e):
    return render_template('errors/error.html', error_code=503, error_message=str(e)), 503


from src.requests import authenticate, roll_number, administrator, event

auth_route = authenticate
roll_number_route = roll_number
admin_route = administrator
event_route = event

import os

from src.app import app


FLASK_PORT = os.environ.get('FLASK_RUN_PORT')
FLASK_HOST = os.environ.get('FLASK_RUN_HOST')
FLASK_DEBUG = os.environ.get('FLASK_DEBUG')

if __name__ == '__main__':
    app.run(
        debug=FLASK_DEBUG,
        port=FLASK_PORT,
        host=FLASK_HOST
    )

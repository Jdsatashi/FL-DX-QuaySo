import os

from src.app import app
from src.utils.env import FLASK_DEBUG, FLASK_PORT, FLASK_HOST

app.logger.info('Starting webapp via development server.')


if __name__ == '__main__':
    app.run(
        debug=FLASK_DEBUG,
        port=FLASK_PORT,
        host=FLASK_HOST
    )

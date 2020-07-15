from flask import Flask
import logging
from os.path import dirname, join, realpath


log_file = "log_wxmeow.log"

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(log_file)
formatter = logging.Formatter(
    '%(asctime)s | %(levelname)s | [%(module)s:%(lineno)d] | %(message)s'
)

file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
app = Flask(__name__, static_url_path=join(dirname(realpath(__file__)), 'static/'))
app.config['SECRET_KEY'] = 'cats will always beat you to the weather'

import meowcast.views



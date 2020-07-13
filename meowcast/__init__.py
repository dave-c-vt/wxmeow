from flask import Flask
from os.path import dirname, join, realpath


app = Flask(__name__, static_url_path=join(dirname(realpath(__file__)), 'static/'))
app.config['SECRET_KEY'] = 'cats will always beat you to the weather'

import meowcast.views

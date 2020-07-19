try:
    from wxmeow import logger
except ImportError:
    print("didn't import logger")
    pass

from wxmeow import app
from flask import url_for
from os import listdir
from os.path import join


def pick_pic(weather=''):
    """return path to random applicable pick

    parameters
    ----------
    weather : str
    
    returns
    -------
    str : filename of pic
    """
    from random import choice

    root = url_for('static', filename='')

    pics = [p for p in listdir(join(root, 'catpics')) if weather.lower() in p.lower()]

    return choice(pics)

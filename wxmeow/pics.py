try:
    from wxmeow import logger
except ImportError:
    print("didn't import logger")
    pass

from flask import url_for
import os
import traceback
from wxmeow import app


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

    wxtext = weather_selector(weather)

    try:
        pics = [p for p in os.listdir(os.path.join(root, 'catpics')) if wxtext in p.lower()]
    except:
        logger.debug(traceback.format_exc())
        pics = os.listdir(os.path.join(root, 'catpics'))

    return choice(pics)


def weather_selector(obs):
    """return weather for pic selector

    parameters
    ----------
    obs : str

    returns
    -------
    str : weather for choosing pic
    """

    sun = {"sun": {"sun", "clear"}}
    rain = {"rain": {"rain", "rain and fog/mist"}}
    cloud = {"cloud": {"cloudy", "cloud", "fog", "mist"}}
    snow = {"snow": {"snow", "ice"}}
    storm = {"thunder": {"thunder", "lightning", "storm", "hail", "tornado"}}

    for i, wx in enumerate([sun, rain, cloud, snow, storm]):
        for key, val in wx.items():
            for condition in wx[key]:
                if condition in obs.lower():
                    print(f"matched {wx[key]}")
                    logger.info(f"matched {wx[key]}")
                    return key

    print(f"could not match {obs.lower()}")
    logger.error(f"could not match {obs.lower()}")
    return False


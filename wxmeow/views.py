try:
    from wxmeow import logger
except ImportError:
    print("didn't import logger")
    pass

from wxmeow import app
from flask import render_template, redirect, url_for


@app.route('/', methods=['GET', 'POST'])
def index():
    from .forms import wxlookup

    form = wxlookup()

    if form.validate_on_submit():
        logger.debug('form redirected!')
        return redirect(url_for('weather', location=form.location.data))

    return render_template(
        'base.html',
        title='MEOWCAST!!',
        form=form
    )


@app.route('/wx/<location>')
def weather(location):
    from .wx2json_noaa import wxmeow
    from .pics import pick_pic

    pick_pic()

    if location != "":
        meow = wxmeow(location)
        pic = pick_pic()
    else:
        return redirect(url_for('index'))

    logger.debug(f'weather for {location} ... ')

    return render_template(
        'base.html',
        title=meow.meowplace,
        wxmeow=meow,
        pic=pic,
    )


@app.errorhandler(404)
def not_found(error):
    return render_template('base.html', title='oops!')

try:
    from meowcast import logger
except ImportError:
    print("didn't import logger")
    pass

from meowcast import app
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
    from .wx2json_noaa import meowcast

    if location != "":
        meow = meowcast(location)
    else:
        return redirect(url_for('index'))

    logger.debug(f'weather for {location} ... ')

    return render_template(
        'base.html',
        title=meow.meowplace,
        meowcast=meow,
    )


@app.errorhandler(404)
def not_found(error):
    return render_template('base.html', title='oops!')

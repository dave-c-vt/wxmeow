try:
    from wxmeow import logger
except ImportError:
    print("didn't import logger")
    pass

from wxmeow import app
from flask import render_template, redirect, url_for
import traceback


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
        try:
            meow = wxmeow(location)
            # self.meowobs need lookup to convert "clear" to "sun", etc.^
            try:
                pic = pick_pic(weather=meow.meowobs)
            except:
                logger.error(f"couldn't get pick for weather: \"{meow.meowobs}\"")
                logger.debug(traceback.format_exc())
                print(f"couldn't get pick for weather: \"{meow.meowobs}\"")
                pic = pick_pic()
        except:
            meow = f"<h2>OH NO!</h2><p>{location} didn't work! is it a place?</p>"

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

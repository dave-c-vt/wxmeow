from meowcast import app
from flask import render_template, redirect


@app.route('/', methods=['GET', 'POST'])
def index():
    from .forms import wxlookup

    form = wxlookup()

    if form.validate_on_submit():
        return redirect(url_for('wx', location=form.location))

    return render_template(
        'base.html',
        title='MEOWCAST!!',
        form=form
    )


@app.route('/wx/<location>')
def weather(location):
    from .wx2json_noaa import meowcast
    meow = meowcast(location)

    return render_template(
        'base.html',
        title=meow.meowplace,
        meowcast=meow,
    )


@app.errorhandler(404)
def not_found(error):
    return render_template('base.html', title='oops!')

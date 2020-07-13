from meowcast import app
from flask import render_template, redirect


@app.route('/')
def index():
    from .forms import wxlookup

    form = wxlookup()

    if form.validate_on_submit():
        return redirect('/wx/<location>')

    return render_template(
        'base.html',
        title='MEOWCAST!!',
        form=form
    )


@app.route('/wx/<zipcode>')
def weather(zipcode):
    from .wx2json_noaa import meowcast
    meow = meowcast(zipcode)

    return render_template(
        'base.html',
        title=meow.meowplace,
        meowcast=meow,
    )


@app.errorhandler(404)
def not_found(error):
    return render_template('base.html', title='oops!')

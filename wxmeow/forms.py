from wtforms import StringField, SubmitField
from flask_wtf import FlaskForm


class wxlookup(FlaskForm):
    location = StringField('location', validators=None, description='enter location')
    submit = SubmitField('MEOWCAST!!')

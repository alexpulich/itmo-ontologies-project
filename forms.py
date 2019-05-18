from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, SubmitField
from wtforms.validators import DataRequired


class SearchForm(FlaskForm):
    vk_id = StringField('VK id', validators=[DataRequired()])
    name = BooleanField('Use name')
    date = BooleanField('Use date')
    submit = SubmitField('Search!')

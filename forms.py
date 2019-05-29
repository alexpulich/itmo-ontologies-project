from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, SubmitField, RadioField
from wtforms.validators import DataRequired


class SearchForm(FlaskForm):
    vk_id = StringField('VK id', validators=[DataRequired()])
    api = RadioField('API', choices=[('dbpedia', 'DBPedia'), ('wikidata', 'WikiData')], default='dbpedia')
    name = BooleanField('Use name')
    date = BooleanField('Use date')
    age = BooleanField('Use age')
    submit = SubmitField('Search')

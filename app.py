import random
import re
import string
import json
import os

import vk_api
import requests

from flask import Flask, render_template
from flask_wtf import FlaskForm
from transliterate import translit
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

ENDPOINT = 'http://dbpedia.org/sparql'
RU_REGEXP = re.compile(r'[a-яА-Я]+')
app = Flask(__name__)
app.config['SECRET_KEY'] = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))
app.config['VK_LOGIN'] = os.environ.get('VK_LOGIN')
app.config['VK_PASSWORD'] = os.environ.get('VK_PASSOWRD')

vk_session = vk_api.VkApi(app.config['VK_LOGIN'], app.config['VK_PASSWORD'])
vk_session.auth()
vk = vk_session.get_api()


def get_name_query(name, date, lang='ru'):
    return ('SELECT DISTINCT * where { '
            '?s foaf:givenName "%s"@%s; '
            'foaf:name ?full_name; '
            'dbo:birthDate ?date. '
            'OPTIONAL { ?s dbo:thumbnail ?picture }'
            'FILTER(REGEX(?date, "%s"))'
            '}' % (name, lang, date))


@app.route('/', methods=['GET', 'POST'])
def index():
    form = SearchForm()
    data = None
    queries = []
    if form.validate_on_submit():
        user = vk.users.get(
            user_ids=[form.vk_id.data],
            fields='city,universities,sex,bdate'
        )
        if RU_REGEXP.match(user[0]['first_name']):
            first_name = translit(user[0]['first_name'], reversed=True)
        else:
            first_name = user[0]['first_name']

        d, m, _ = user[0]['bdate'].split('.')
        if int(d) < 10:
            d = '0' + d
        if int(m) < 10:
            m = '0' + m
        b_date = f'-{m}-{d}'
        query = get_name_query(first_name, b_date, 'en')
        queries = [query]
        data = requests.get(f"{ENDPOINT}?output=json&query={query}")
        try:
            data = data.json()
        except json.decoder.JSONDecodeError:
            data = data.text

    return render_template('index.html', form=form, data=data, queries=queries)


class SearchForm(FlaskForm):
    vk_id = StringField('VK id', validators=[DataRequired()])
    submit = SubmitField('Search!')

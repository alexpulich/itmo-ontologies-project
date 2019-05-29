import random
import re
import string
import os
import collections
import transliterate

from flask import Flask, render_template

import vk_api
import forms
import api.dbpedia
import api.wikidata

RU_REGEXP = re.compile(r'[a-яА-Я]+')

app = Flask(__name__)
app.config['SECRET_KEY'] = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))

provided_vk_login = os.environ.get('VK_LOGIN')
provided_vk_pwd = os.environ.get('VK_PASSWORD')

if provided_vk_login and provided_vk_pwd:
    app.config['VK_LOGIN'] = provided_vk_login
    app.config['VK_PASSWORD'] = provided_vk_pwd
else:
    app.config['VK_LOGIN'] = 'user_v2qjJtQM7SOFuvz'
    app.config['VK_PASSWORD'] = 'ibbcc5O9QOpFn26'

vk_session = vk_api.VkApi(app.config['VK_LOGIN'], app.config['VK_PASSWORD'])
vk_session.auth()
vk = vk_session.get_api()

@app.route('/', methods=['GET', 'POST'])
def index():
    form = forms.SearchForm()
    data = None
    countries = collections.Counter([])
    if form.validate_on_submit():

        try:
            user = vk.users.get(
                user_ids=[form.vk_id.data],
                fields='city,universities,sex,bdate'
            )
        except vk_api.exceptions.ApiError:
            user = None

        if user is None:
            data = []
        else:
            if RU_REGEXP.match(user[0]['first_name']):
                first_name = transliterate.translit(user[0]['first_name'], reversed=True).replace("'", '')
            else:
                first_name = user[0]['first_name']

            birthdate_raw = user[0].get('bdate')
            birthdate = birthdate_raw.split('.') if birthdate_raw else (0, 0, 0)

            use_date = birthdate_raw is not None and form.date.data
            use_age  = birthdate_raw is not None and form.age.data

            if form.api.data == 'wikidata':
                data = api.wikidata.search_people(first_name, birthdate, form.name.data, use_date, use_age, 'en')
            elif form.api.data == 'dbpedia':
                data = api.dbpedia.search_people(first_name, birthdate, form.name.data, use_date, use_age, 'en')
            else:
                data = None

            if data is not None:
                countries = collections.Counter([item['country_name']['value'] for item in data if 'country_name' in item])
            else:
                countries = collections.Counter()

    return render_template('index.html', form=form, data=data, countries=countries)


@app.route('/person/<path:uri>', methods=['GET'])
def person(uri):
    profile = api.dbpedia.get_bio(uri)
    father = api.dbpedia.get_relative(uri, 'dbp:father')
    mother = api.dbpedia.get_relative(uri, 'dbp:mother')
    spouse = api.dbpedia.get_relative(uri, 'dbo:spouse')
    relatives = api.dbpedia.get_inverse_relatives(uri, 'dbo:relative')
    siblings = api.dbpedia.get_relatives(uri, 'dbp:siblings')
    return render_template('person.html', profile=profile, father=father, mother=mother,
                           spouse=spouse, siblings=siblings, relatives=relatives)
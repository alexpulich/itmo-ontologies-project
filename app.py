import random
import re
import string
import os
from collections import Counter

import vk_api

from flask import Flask, render_template, current_app
from flask_wtf import FlaskForm
from transliterate import translit
from wtforms import BooleanField, StringField, SubmitField
from wtforms.validators import DataRequired
from SPARQLWrapper import SPARQLWrapper, JSON

ENDPOINT = 'http://dbpedia.org/sparql'
RU_REGEXP = re.compile(r'[a-яА-Я]+')

app = Flask(__name__)
app.config['SECRET_KEY'] = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))
sparql = SPARQLWrapper(ENDPOINT)

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


def search_people(name, date, lang='ru', use_name=True, use_date=True):
    query = '''SELECT DISTINCT * where { 
        ?person foaf:name ?full_name;
        dbo:birthDate ?date. '''

    if use_name:
        query += '?person foaf:givenName "%s"@%s. ' % (name, lang)

    query += 'OPTIONAL { ?person dbo:thumbnail ?picture } '

    query += '''OPTIONAL { 
    ?person dbo:birthPlace ?country. 
    ?country rdf:type dbo:Country; 
    rdfs:label ?country_name } '''

    if use_date:
        query += 'FILTER(REGEX(?date, "%s")) ' % date

    query += 'FILTER(lang(?country_name) = "en") '

    query += '} GROUP BY ?person ?full_name'

    current_app.logger.error(query)

    sparql.setQuery(query)

    sparql.setReturnFormat(JSON)
    return sparql.query().convert()['results']['bindings']


def get_relative(person, relation):
    if person.startswith('http://dbpedia.org/resource/'):
        person = person.replace('http://dbpedia.org/resource/', 'dbr:')
    else:
        return None

    sparql.setQuery(
        """
        select *
        where {
        %s %s ?relative.
        ?relative foaf:name ?full_name;
        dbo:birthDate ?date.
        OPTIONAL { ?relative dbo:thumbnail ?picture }
        }
        GROUP BY ?relative ?full_name
        LIMIT 1
        """ % (person, relation)
    )

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()['results']['bindings']
    return results[0] if len(results) > 0 else None


def get_relatives(person, relation):
    if person.startswith('http://dbpedia.org/resource/'):
        person = person.replace('http://dbpedia.org/resource/', 'dbr:')
    else:
        return None

    sparql.setQuery(
        """
        select *
        where {
        %s %s ?relative.
        ?sibling foaf:name ?full_name;
        dbo:birthDate ?date.
        OPTIONAL { ?relative dbo:thumbnail ?picture }
        }
        GROUP BY ?relative ?full_name
        LIMIT 1
        """ % (person, relation)
    )

    sparql.setReturnFormat(JSON)
    return sparql.query().convert()['results']['bindings']


@app.route('/', methods=['GET', 'POST'])
def index():
    form = SearchForm()
    data = None
    countries = Counter([])
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
                first_name = translit(user[0]['first_name'], reversed=True).replace("'", '')
            else:
                first_name = user[0]['first_name']

            birthdate = user[0]['bdate'].split('.')
            d = birthdate[0]
            m = birthdate[1]

            if int(d) < 10:
                d = '0' + d
            if int(m) < 10:
                m = '0' + m
            b_date = f'-{m}-{d}'
            data = search_people(first_name, b_date, 'en', form.name.data, form.date.data)

            countries = Counter([item['country_name']['value'] for item in data if 'country_name' in item])
            current_app.logger.error(countries)

    return render_template('index.html', form=form, data=data, countries=countries)


@app.route('/person/<path:uri>', methods=['GET'])
def person(uri):
    father = get_relative(uri, 'dbp:father')
    mother = get_relative(uri, 'dbp:mother')
    spouse = get_relative(uri, 'dbo:spouse')
    siblings = get_relatives(uri, 'dbp:siblings')
    return render_template('person.html', father=father, mother=mother,
                           spouse=spouse, siblings=siblings)


class SearchForm(FlaskForm):
    vk_id = StringField('VK id', validators=[DataRequired()])
    name = BooleanField('Use name')
    date = BooleanField('Use date')
    submit = SubmitField('Search!')

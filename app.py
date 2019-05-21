import random
import re
import string
import os
from collections import Counter

import vk_api

from flask import Flask, render_template, current_app
from transliterate import translit
from SPARQLWrapper import SPARQLWrapper, JSON

from decorators import prefix_uri
from forms import SearchForm

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
    if not use_name and not use_date:
        use_name = True
        use_date = True

    query = '''SELECT DISTINCT sample(?person) as ?person, 
    sample(?full_name) as ?full_name, 
    sample(?date) as ?date, 
    sample(?country_name) as ?country_name,
    sample(?picture) as ?picture 
    where { 
        ?person foaf:name ?full_name;
        dbo:birthDate ?date. '''

    if use_name:
        query += '?person foaf:givenName "%s"@%s. ' % (name, lang)

    query += '\nOPTIONAL { ?person dbo:thumbnail ?picture } '

    query += '''\nOPTIONAL { 
        ?person dbo:birthPlace ?country. 
        ?country rdf:type dbo:Country; 
        rdfs:label ?country_name } '''

    if use_date:
        query += '\nFILTER(REGEX(?date, "%s")) ' % date

    query += '\nFILTER(lang(?country_name) = "en")\nFILTER(lang(?country_name) = "en") '

    query += '}\nGROUP BY ?person ?full_name\nORDER BY ?full_name'

    sparql.setQuery(query)

    sparql.setReturnFormat(JSON)
    return sparql.query().convert()['results']['bindings']


@prefix_uri
def get_relative(person, relation):
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

@prefix_uri
def get_inverse_relatives(person, relation):
    sparql.setQuery(
        """
        select *
        where {
        ?relative %s %s;
        foaf:name ?full_name;
        dbo:birthDate ?date.
        OPTIONAL { ?relative dbo:thumbnail ?picture }
        }
        GROUP BY ?relative ?full_name
        LIMIT 1
        """ % (relation, person)
    )

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()['results']['bindings']
    return results


@prefix_uri
def get_relatives(person, relation):
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


@prefix_uri
def get_bio(uri):
    sparql.setQuery(
        '''SELECT * WHERE {{
        {0} foaf:name ?name.
        OPTIONAL {{{0} foaf:gender ?gender}}
        OPTIONAL {{{0} dbo:abstract ?abstract}}
        OPTIONAL {{{0} dbo:birthDate ?date}}
        OPTIONAL {{
        {0} dbo:birthPlace ?country.
        ?country rdf:type dbo:Country;
        rdfs:label ?country_name
        }}
        OPTIONAL {{
        {0} dbo:birthPlace ?city.
        ?city rdf:type dbo:City;
        rdfs:label ?city_name
        }}
        OPTIONAL {{{0} dbo:thumbnail ?image}}
        FILTER(lang(?gender) = 'en')
        FILTER(lang(?name) = 'en')
        FILTER(lang(?abstract) = 'en')
        FILTER(lang(?country_name) = 'en')
        FILTER(lang(?city_name) = 'en')
        }}
        LIMIT 1
        '''.format(uri)
    )

    sparql.setReturnFormat(JSON)
    data = sparql.query().convert()['results']['bindings']
    return data[0] if len(data) > 0 else {}


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

    return render_template('index.html', form=form, data=data, countries=countries)


@app.route('/person/<path:uri>', methods=['GET'])
def person(uri):
    profile = get_bio(uri)
    father = get_relative(uri, 'dbp:father')
    mother = get_relative(uri, 'dbp:mother')
    spouse = get_relative(uri, 'dbo:spouse')
    relatives = get_inverse_relatives(uri, 'dbo:relative')
    siblings = get_relatives(uri, 'dbp:siblings')
    return render_template('person.html', profile=profile, father=father, mother=mother,
                           spouse=spouse, siblings=siblings, relatives=relatives)
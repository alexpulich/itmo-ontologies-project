from functools import wraps
import SPARQLWrapper

ENDPOINT = 'http://dbpedia.org/sparql'
dbpedia_sparql = SPARQLWrapper.SPARQLWrapper(ENDPOINT)

def prefix_uri(func):
    @wraps(func)
    def prefix(*args, **kwargs):
        if args[0].startswith('http://dbpedia.org/resource/'):
            modified_uri = args[0].replace('http://dbpedia.org/resource/', 'dbr:')
            new_args = (modified_uri,) + args[1:]
            return func(*new_args, **kwargs)

        return lambda x: None

    return prefix


def search_people(name, date, use_name, use_date, use_age, lang='ru'):
    if not use_name and not use_date and not use_age:
        return None

    d = date[0]
    m = date[1]
    y = date[2]

    if int(d) < 10:
        d = '0' + str(d)
    if int(m) < 10:
        m = '0' + str(m)

    b_date = ''
    if use_age:
        b_date += str(y)
    if use_date:
        b_date += f'-{m}-{d}'

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

    if b_date:
        query += '\nFILTER(REGEX(?date, "%s")) ' % b_date

    query += '\nFILTER(lang(?country_name) = "en")\nFILTER(lang(?country_name) = "en") '

    query += '}\nGROUP BY ?person ?full_name\nORDER BY ?full_name'

    dbpedia_sparql.setQuery(query)

    dbpedia_sparql.setReturnFormat(SPARQLWrapper.JSON)
    return dbpedia_sparql.query().convert()['results']['bindings']


@prefix_uri
def get_relative(person, relation):
    dbpedia_sparql.setQuery(
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

    dbpedia_sparql.setReturnFormat(SPARQLWrapper.JSON)
    results = dbpedia_sparql.query().convert()['results']['bindings']
    return results[0] if len(results) > 0 else None

@prefix_uri
def get_inverse_relatives(person, relation):
    dbpedia_sparql.setQuery(
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

    dbpedia_sparql.setReturnFormat(SPARQLWrapper.JSON)
    results = dbpedia_sparql.query().convert()['results']['bindings']
    return results


@prefix_uri
def get_relatives(person, relation):
    dbpedia_sparql.setQuery(
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

    dbpedia_sparql.setReturnFormat(SPARQLWrapper.JSON)
    return dbpedia_sparql.query().convert()['results']['bindings']


@prefix_uri
def get_bio(uri):
    dbpedia_sparql.setQuery(
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

    dbpedia_sparql.setReturnFormat(SPARQLWrapper.JSON)
    data = dbpedia_sparql.query().convert()['results']['bindings']
    return data[0] if len(data) > 0 else {}

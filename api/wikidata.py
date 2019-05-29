import SPARQLWrapper

ENDPOINT = 'http://query.wikidata.org/bigdata/namespace/wdq/sparql'
wd_sparql = SPARQLWrapper.SPARQLWrapper(ENDPOINT)

father_relation = 'wdt:P22'
mother_relation = 'wdt:P25'
sinblings_relation = 'wdt:P3373'


def search_people(name, birthdate, use_name, use_date, use_age, lang='ru'):
    if not use_name and not use_date and not use_age:
        return None

    day = None
    month = None
    year = None

    if len(birthdate) > 1:
        day = birthdate[0]
        month = birthdate[1]

    if len(birthdate) == 3:
        year = birthdate[2]

    if use_age and year is None:
        return []
    if use_date and (month is None and day is None):
        return []

    query = '''SELECT 
    (SAMPLE(?person) as ?person) 
    (SAMPLE(?date) AS ?date) 
    (SAMPLE(?full_name) as ?full_name) 
    (SAMPLE(?country_name) as ?country_name) 
    (SAMPLE(?picture) as ?picture)
    (COUNT(?prop) as ?props) 
                WHERE {
                    ?person wdt:P31 wd:Q5. 
                    ?person wdt:P569 ?date.
                    ?person rdfs:label ?full_name.
                    ?person ?prop ?x.
    '''

    if use_name:
        query += '?person wdt:P735 ?name_label. ?name_label rdfs:label "%s"@%s.' % (name, lang)

    query += '\nOPTIONAL { ?person wdt:P18 ?picture } '
    query += '\nOPTIONAL { ?person wdt:P27 ?country. ?country rdfs:label ?country_name }'

    query += '''\nOPTIONAL { 
        ?person wd:P19 ?place.
         
        ?place 
        rdfs:label ?birthPlace } '''

    if use_date:
        query += '\n FILTER(DAY(?date)=%s && MONTH(?date)=%s)' % (day, month)

    if use_age:
        query += '\n FILTER(YEAR(?date)=%s)' % (year)

    query += '\n FILTER(langMatches(lang(?full_name),"%s"))' % (lang)
    query += '\n FILTER(langMatches(lang(?country_name),"%s"))' % (lang)

    query += '} GROUP BY ?person ORDER BY DESC(?props) LIMIT 100'

    wd_sparql.setQuery(query)

    wd_sparql.setReturnFormat(SPARQLWrapper.JSON)
    sparql_result = wd_sparql.query()
    converted_result = sparql_result.convert()
    results = converted_result['results']['bindings']

    return results
    ''' FIXME: это костыль, если не придумаем запрос
    index = []
    set_results = []
    for result in results:
        if result['person'] not in index:
            index.append(result['person'])
            set_results.append(result)
    return set_results
    '''


def get_relative(person, relation):
    query = '''
        SELECT distinct 
            ?relative
            ?date
            ?full_name
            ?picture 
            WHERE {
              wd:%s %s ?relative. 
              wd:%s wdt:P31 wd:Q5. 
              ?relative wdt:P569 ?date.
              ?relative rdfs:label ?full_name.
            
              OPTIONAL { ?relative wdt:P18 ?picture }
              FILTER( LangMatches(lang(?full_name),'en'))
        }''' % (person, relation, person)

    wd_sparql.setQuery(query)
    wd_sparql.setReturnFormat(SPARQLWrapper.JSON)
    results = wd_sparql.query().convert()['results']['bindings']
    return results[0] if len(results) > 0 else None


def get_relatives(person, relation):
    wd_sparql.setQuery('''
    SELECT
    distinct
    ?relative
    ?date
    ?full_name
    ?picture
    WHERE
    {
        wd:%s %s ?relative.
        wd:%s wdt:P31 wd:Q5.
        ?relative wdt:P569 ?date.
        ?relative rdfs:label ?full_name.

        OPTIONAL
            { ?relative wdt:P18 ?picture} 
        
        FILTER(LangMatches(lang(?full_name), 'en'))
    }''' % (person, relation, person))

    wd_sparql.setReturnFormat(SPARQLWrapper.JSON)
    results = wd_sparql.query().convert()['results']['bindings']
    return results


def get_inverse_relatives(person, relation):
    wd_sparql.setQuery('''
    SELECT
    distinct
    ?relative
    ?date
    ?full_name
    ?picture
    WHERE
    {
        ?relative wd:%s %s.
        wd:%s wdt:P31 wd:Q5.
        ?relative wdt:P569 ?date.
        ?relative rdfs:label ?full_name.

        OPTIONAL
            { ?relative wdt:P18 ?picture} 

        FILTER(LangMatches(lang(?fullname), 'en'))
    }''' % (person, relation, person))

    wd_sparql.setReturnFormat(SPARQLWrapper.JSON)
    results = wd_sparql.query().convert()['results']['bindings']
    return results

def get_bio(person):
    wd_sparql.setQuery('''
        SELECT distinct 
            ?person
            ?date
            ?name
            ?picture 
            ?gender
            ?place
            WHERE {
              wd:%s wdt:P31 wd:Q5. 
              wd:%s rdfs:label ?name.
              
              wd:%s wdt:P569 ?date.
              OPTIONAL{
              wd:%s wdt:P21 ?genderObj.
              ?genderObj rdfs:label ?gender.
              FILTER(LangMatches(lang(?gender), 'en'))
              }
              OPTIONAL{
              wd:%s wdt:P19 ?placeObj.
              ?placeObj rdfs:label ?place.
              FILTER(LangMatches(lang(?place), 'en'))
              }
              
              OPTIONAL { wd:%s wdt:P18 ?picture }
              
              FILTER(LangMatches(lang(?name), 'en'))
          }
            LIMIT 1
    ''' % (person,person,person,person,person,person))
    wd_sparql.setReturnFormat(SPARQLWrapper.JSON)
    data = wd_sparql.query().convert()['results']['bindings']
    return data[0] if len(data) > 0 else {}


def get_entity_key(name):
    #'http://www.wikidata.org/entity/Q123'
    #Q123
    return name[31:]

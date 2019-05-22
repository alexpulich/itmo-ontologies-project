import SPARQLWrapper

ENDPOINT = 'http://query.wikidata.org/bigdata/namespace/wdq/sparql'
wd_sparql = SPARQLWrapper.SPARQLWrapper(ENDPOINT)

father_relation = 'wdt:P22'
mother_relation = 'wdt:P25'
sinblings_relation = 'wdt:P3373'


def search_people(name, birthdate, use_name, use_date, use_age, lang='ru'):
    if not use_name and not use_date and not use_age:
        return None

    day = birthdate[0]
    month = birthdate[1]

    query = '''SELECT distinct 
                ?person ?date ?full_name ?country_name ?picture
                WHERE {
                    ?person wdt:P31 wd:Q5. 
                    ?person wdt:P569 ?date.
                    ?person rdfs:label ?full_name.
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

    query += '\n FILTER(langMatches(lang(?full_name),"%s"))' % (lang)
    query += '\n FILTER(langMatches(lang(?country_name),"%s"))' % (lang)

    query += '}'

    wd_sparql.setQuery(query)

    wd_sparql.setReturnFormat(SPARQLWrapper.JSON)
    sparql_result = wd_sparql.query()
    converted_result = sparql_result.convert()
    return converted_result['results']['bindings']


def get_relative(person, relation):
    query = '''
        SELECT distinct 
            ?relative
            ?date
            ?fullname
            ?picture 
            WHERE {
              wd:%s %s ?relative. 
              wd:%s wdt:P31 wd:Q5. 
              ?relative wdt:P569 ?date.
              ?relative rdfs:label ?fullname.
            
              OPTIONAL { ?relative wdt:P18 ?picture }
              FILTER( LangMatches(lang(?fullname),'en'))
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
    ?fullname
    ?picture
    WHERE
    {
        wd:%s %s ?relative.
        wd:%s wdt:P31 wd:Q5.
        ?relative wdt:P569 ?date.
        ?relative rdfs:label ?fullname.

        OPTIONAL
            { ?relative wdt:P18 ?picture} 
        
        FILTER(LangMatches(lang(?fullname), 'en'))
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
    ?fullname
    ?picture
    WHERE
    {
        ?relative wd:%s %s.
        wd:%s wdt:P31 wd:Q5.
        ?relative wdt:P569 ?date.
        ?relative rdfs:label ?fullname.

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
            ?fullname
            ?picture 
            ?gender
            ?place
            WHERE {
              ?person rdfs:label ?fullname.
              wd:%s wdt:P31 wd:Q5. 
              wd:%s rdfs:label ?fullname.
              
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
              
              FILTER(LangMatches(lang(?fullname), 'en'))
          }
  
    ''' % (person,person,person,person,person,person))
    wd_sparql.setReturnFormat(SPARQLWrapper.JSON)
    data = wd_sparql.query().convert()['results']['bindings']
    return data[0] if len(data) > 0 else {}


def get_entity_key(name):
    #'http://www.wikidata.org/entity/Q123'
    #Q123
    return name[31:]

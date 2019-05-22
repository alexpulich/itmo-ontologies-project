from SPARQLWrapper import SPARQLWrapper, JSON

ENDPOINT = 'http://query.wikidata.org/bigdata/namespace/wdq/sparql'

sparql = SPARQLWrapper(ENDPOINT)

father_relation = 'wdt:P22'
mother_relation = 'wdt:P25'
sinblings_relation = 'wdt:P3373'

def search_people(name, day, month, lang='ru', use_name=True, use_date=True):
    if not use_name and not use_date:
        return None

    query = '''SELECT distinct 
                ?person ?date ?full_name 
                WHERE {
                    ?person wdt:P31 wd:Q5. 
                    ?person wdt:P569 ?date.
                    ?person rdfs:label ?full_name.
    '''

    if use_name:
        query += '?person rdfs:label "%s"@%s. ' % (name, lang)

    query += '\nOPTIONAL { ?person wdt:P18 ?picture } '

    query += '''\nOPTIONAL { 
        ?person wd:P19 ?place. 
        ?place 
        rdfs:label ?birthPlace } '''

    if use_date:
        query += '\n FILTER(DAY(?date)=%s && MONTH(?date)=%s)' % (day, month)

    query += '\n FILTER(langMatches(lang(?full_name),"%s"))' % lang

    query += '}'

    sparql.setQuery(query)

    sparql.setReturnFormat(JSON)
    return sparql.query().convert()['results']['bindings']


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

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()['results']['bindings']
    return results[0] if len(results) > 0 else None


def get_relatives(person, relation):
    sparql.setQuery('''
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

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()['results']['bindings']
    return results


def get_inverse_relatives(person, relation):
    sparql.setQuery('''
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

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()['results']['bindings']
    return results

def get_bio(person):
    sparql.setQuery('''
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
    sparql.setReturnFormat(JSON)
    data = sparql.query().convert()['results']['bindings']
    return data[0] if len(data) > 0 else {}

def get_entity_key(name):
    #'http://www.wikidata.org/entity/Q123'
    #Q123
    return name[31:]

#print(search_people('Pavel Durov',10,10,'en'))

#print(get_relative('Q149067', father_relation))

#print(get_relatives('Q149067', sinblings_relation))

#print(get_bio('Q149067'))

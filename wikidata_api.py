from SPARQLWrapper import SPARQLWrapper, JSON

ENDPOINT = 'http://query.wikidata.org/bigdata/namespace/wdq/sparql'

sparql = SPARQLWrapper(ENDPOINT)


def search_people(name, day, month, lang='ru', use_name=True, use_date=True):
    if not use_name and not use_date:
        return None

    query = '''SELECT distinct 
                ?person ?date, ?full_name 
                WHERE {
                    ?person wdt:P31 wd:Q5. 
                    ?person wdt:P569 ?date.
                    ?person rdfs:label ?full_name.
    '''

    if use_name:
        query += '?person rdfs:label "%s"@%s. ' % (name, lang)

    query += '\nOPTIONAL { ?person wd:P18 ?picture } '

    query += '''\nOPTIONAL { 
        ?person wd:P19 ?place. 
        ?place 
        rdfs:label ?birthPlace } '''

    if use_date:
        query += '\n FILTER(DAY(?date)=%s && MONTH(?date)=%s)' % (day, month)

    query += '}'

    sparql.setQuery(query)

    sparql.setReturnFormat(JSON)
    return sparql.query().convert()['results']['bindings']

print(search_people('Pavel Durov',10,10,'en'))
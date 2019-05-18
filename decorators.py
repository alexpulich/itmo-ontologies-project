from functools import wraps


def prefix_uri(func):
    @wraps(func)
    def prefix(*args, **kwargs):
        if args[0].startswith('http://dbpedia.org/resource/'):
            modified_uri = args[0].replace('http://dbpedia.org/resource/', 'dbr:')
            new_args = (modified_uri,) + args[1:]
            return func(*new_args, **kwargs)

        return lambda x: None

    return prefix

import json
import requests
import logging
log = logging.getLogger(__name__)

global ELASTIC_SEARCH_OBJ
ELASTIC_SEARCH_OBJ = {'enable': False}

def init_elastic_search(host, port, max_suggest, user, password, isProduction):
    global ELASTIC_SEARCH_OBJ
    ELASTIC_SEARCH_OBJ['host'] = host + ':' + port
    ELASTIC_SEARCH_OBJ['enable'] = True
    ELASTIC_SEARCH_OBJ['max'] = max_suggest
    ELASTIC_SEARCH_OBJ['user'] = user
    ELASTIC_SEARCH_OBJ['pass'] = password
    ELASTIC_SEARCH_OBJ['server'] = 'production' if isProduction else 'test'
    

def update_elastic_search_user(display_name, email):
    global ELASTIC_SEARCH_OBJ

    if ELASTIC_SEARCH_OBJ['enable']:
        server = ELASTIC_SEARCH_OBJ['server']
        payload = {
            'user': display_name,
            'email': email,
            'suggest': display_name.split(' ') + [email],
            'server': server
        }
    
        auth = (
            ELASTIC_SEARCH_OBJ['user'],
            ELASTIC_SEARCH_OBJ['pass'],
        )
        url = ELASTIC_SEARCH_OBJ['host']
        url += '/oice/user/' + server + ':' + email
        try:
            requests.post(url, auth=auth, data=json.dumps(payload))
        except Exception as e:
            log.error('Search user error: ' + str(e))


def do_elastic_search_user(prefix):
    global ELASTIC_SEARCH_OBJ

    if ELASTIC_SEARCH_OBJ['enable']:
        payload = {
            'query': {
                'bool': {
                    'must': [
                        {
                            'query_string': {
                                'query': prefix + '*',
                                'fields': [
                                    'user',
                                    'email^2'
                                ],
                                'analyzer': 'standard',
                                'default_operator': 'AND'
                            }
                        },
                        {
                            'query_string': {
                                'query': ELASTIC_SEARCH_OBJ['server'],
                                'fields': ['server']
                            }
                        },
                        {
                            'query_string': {
                                'query': 'email:*@*'
                            }
                        }
                    ]
                }
            }
        }
    
        param = {
            'size': ELASTIC_SEARCH_OBJ['max'],
            '_source_include': 'user,email'
        }
        auth = (
            ELASTIC_SEARCH_OBJ['user'],
            ELASTIC_SEARCH_OBJ['pass'],
        )
        url = ELASTIC_SEARCH_OBJ['host']
        url += '/oice/user/_search'
        try:
            res = requests.get(url, auth=auth, params=param, data=json.dumps(payload))
            content = json.loads(res.text)

            emails = []
            email_score = {}
            for option in content['hits']['hits']:
                email = option['_source']['email']
                emails.append(email)
                email_score[email] = option['_score']

            # return list of email
            return emails,email_score
        except Exception as e:
            log.error('Search user error: ' + str(e))
    
    return [],{}

import json
import requests
import logging
from aws_requests_auth.aws_auth import AWSRequestsAuth

log = logging.getLogger(__name__)

global ELASTIC_SEARCH_OBJ
ELASTIC_SEARCH_OBJ = {'enable': False}
global auth

def init_elastic_search(
    host, max_suggest, aws_access_key, aws_secret_key, aws_region, isProduction
):
    global ELASTIC_SEARCH_OBJ
    ELASTIC_SEARCH_OBJ['host'] = host
    ELASTIC_SEARCH_OBJ['enable'] = True
    ELASTIC_SEARCH_OBJ['max'] = max_suggest
    ELASTIC_SEARCH_OBJ['server'] = 'production' if isProduction else 'test'

    global auth
    auth = AWSRequestsAuth(aws_access_key=aws_access_key,
                       aws_secret_access_key=aws_secret_key,
                       aws_host=host.split('://')[-1],
                       aws_region=aws_region,
                       aws_service='es')

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
        url = ELASTIC_SEARCH_OBJ['host']
        url += '/oice/user/' + server + ':' + email
        try:
            requests.post(url, auth=auth, json=payload)
        except Exception as e:
            log.error(e)
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

        url = ELASTIC_SEARCH_OBJ['host']
        url += '/oice/user/_search'
        try:
            res = requests.get(url, auth=auth, json=payload)
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
            log.error(e)
            log.error('Search user error: ' + str(e))
    
    return [],{}

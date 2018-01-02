import os
from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from sqlalchemy import engine_from_config
from pyramid.security import ALL_PERMISSIONS
from pyramid.security import Allow
from pyramid.renderers import JSONP
import pyramid_safile
import stripe
import logging
import firebase_admin
from firebase_admin import credentials
import signal
import sys

from .models import (
    DBSession,
    UserQuery
)
from .models.base import (
    Base,
)

from .views.util.confluent_kafka_log import (
    flush_producer,
)

from .operations.worker import init_worker
log = logging.getLogger(__name__)


class Root(object):
    def __acl__(self):
        acl = [
            (Allow, 'r:user', 'get'),
            (Allow, 'r:paid', 'get'),
            (Allow, 'r:paid', 'paid_get'),
            (Allow, 'r:admin', ALL_PERMISSIONS)
        ]
        return acl

    def __init__(self, request):
        self.request = request


def groupfinder(userid, request):
    user = UserQuery(DBSession).fetch_user_by_email(userid).first()
    if user:
        return ['r:' + user.role]

def sigint_handler(signal, frame):
    flush_producer()
    sys.exit(0)

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    authn_policy = AuthTktAuthenticationPolicy(
        settings['auth.secret'],
        timeout=int(settings['auth.timeout']),
        max_age=int(settings['auth.timeout']),
        callback=groupfinder
    )
    authz_policy = ACLAuthorizationPolicy()
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    config = Configurator(
        settings=settings,
        authentication_policy=authn_policy,
        authorization_policy=authz_policy,
        root_factory=Root
    )

    if config.get_settings().get('cors.preflight', None) == 'true':
        config.include('.cors')
        config.add_cors_preflight_handler()

    config.include("cornice")
    config.include('pyramid_mako')
    config.add_static_view('static', 'static', cache_max_age=3600)
    upload_dir = os.path.abspath(settings['upload_dir'])
    config.add_static_view('upload', upload_dir, cache_max_age=3600)
    config.add_renderer('jsonp', JSONP(param_name='callback'))

    config.scan(ignore=['modmod.scripts','modmod.tests'])
    config.include('.config')
    config.include('modmod.views')
    config.include('modmod.views.util')

    safile_settings = {
        'file.storages': ['fs:'+settings['upload_dir']],
        'fs.'+ settings['upload_dir'] +'.asset_path': '/upload/',
    }

    pyramid_safile.init_factory(safile_settings)

    init_worker(settings, safile_settings)
    
    stripe.api_key = settings['stripe.api_key'];

    if not "CI" in os.environ and os.path.isfile('secret/fbServiceAccountKey.json') :
        cred = credentials.Certificate('secret/fbServiceAccountKey.json')
        default_firebase_app = firebase_admin.initialize_app(cred)

    signal.signal(signal.SIGINT, sigint_handler)
    signal.signal(signal.SIGTERM, sigint_handler)
    signal.signal(signal.SIGHUP, sigint_handler)

    return config.make_wsgi_app()

import logging
import json
from urllib.parse import urlparse

from pyramid.settings import aslist
from sqlalchemy.types import TypeDecorator, Unicode

from .s3 import S3FileHandleFactory
from .fs import FileSystemHandleFactory
from .error import FileHandleError

log = logging.getLogger(__name__)
factory = None


def init_factory(config):
    global factory
    factory = FileHandleFactory(config)


def get_factory():
    global factory
    if factory == None:
        raise TypeError("File Factory not init properly")
    return factory


class FileHandleFactory(object):

    ENGINE_MAP = {
        's3': S3FileHandleFactory,
        'fs': FileSystemHandleFactory
    }

    def __init__(self, config):
        storages = aslist(config['file.storages'])
        log.info("Initializing file storages: %s" % (storages))
        self._engines = {}
        self.engines = []
        for storage in storages:
            self.add_engine(storage, config)

    def add_engine(self, storage, config):
        log.info("Initializing file storage: %s" % (storage))
        url = urlparse(storage)
        try:
            handle_factory = self.ENGINE_MAP[url.scheme]
        except KeyError:
            raise FileHandleError("Storage type is not supported: %s" %
                url.scheme)
        else:
            factory = handle_factory(url, config)
            self._engines[url.scheme] = factory
            self.engines.append(factory)

    @property
    def default_engine(self):
        return self.engines[0]

    def __getitem__(self, name):
        try:
            return self._engines[name]
        except KeyError:
            raise FileHandleError("Storage type is not supported: %s" %
                name)

    def create_handle(self, original_filename, fp, engine=None):
        if engine is None:
            engine = self.default_engine
        return engine.create_handle(original_filename, fp)

    def restore_handle(self, descriptor):
        storage = descriptor['storage']
        obj = self[storage].from_descriptor(descriptor)
        return obj


class FileHandleStore(TypeDecorator):
    """Represents an immutable structure as a json-encoded string.

    Usage::

        FileHandleStore(255)

    """

    impl = Unicode(255)

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value.descriptor)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            descriptor = json.loads(value)
            handle = factory.restore_handle(descriptor)
            return handle
        return None

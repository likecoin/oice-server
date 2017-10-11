import os
import sys
import tempfile
import logging
import shutil
import hashlib
import base64
from datetime import datetime
from rq import Queue, use_connection
from redis import Redis
from google.cloud import storage
import requests
from sqlalchemy import engine_from_config
import pyramid_safile
import transaction
import json
from ..models import (
    AssetQuery,
    Block,
    DBSession,
    CharacterQuery,
    LibraryQuery,
    Macro,
    OiceQuery,
    ProjectExport,
    UserQuery,
)
from .block import ensure_block_default_value, update_block_attributes
from .script_exporter import ScriptExporter, KSScriptBuilder
from .script_import_parser import parse_script, ScriptImportParserError
from ..views.util import (
    update_user_mailchimp_stage,
    init_slack,
    send_oice_publish_message_into_slack
)

log = logging.getLogger(__name__)

settings = None
safile_settings = None


def init_worker(_settings, _safile_settings):
    global settings
    global safile_settings
    settings = _settings
    safile_settings = _safile_settings


def run_export(_settings,
               _safile_settings,
               story_export_id):

    pyramid_safile.init_factory(_safile_settings)

    engine = engine_from_config(_settings)
    DBSession.configure(bind=engine)

    with transaction.manager:
        story_export = DBSession.query(ProjectExport) \
                                .filter(ProjectExport.id == story_export_id) \
                                .one()

        characters = CharacterQuery(DBSession).fetch_by_oice(story_export.oice)

        temp_zip = os.path.join(tempfile.mkdtemp(), 'data.zip')
        exporter = ScriptExporter(
            _settings["o2.resize_script"],
            story_export.oice,
            temp_zip,
            characters=characters,
        )

        exporter.export()

        factory = pyramid_safile.get_factory()
        handle = factory.create_handle('data.zip', open(temp_zip, 'rb'))

        story_export.exported_files = handle

    send_result_request('export', {
        'id': story_export_id,
        'message': 'ok'
    })


class ExportWorker(object):

    def __init__(self, story_export_id):
        super().__init__()

        self.story_export_id = story_export_id

    def run(self):
        global settings
        global safile_settings

        redis = Redis(settings["redis.host"], settings["redis.port"], password=settings["redis.password"])
        use_connection(redis)
        q = Queue()

        result = q.enqueue(
            run_export,
            args=(
                settings,
                safile_settings,
                self.story_export_id,
            ),
            timeout=600
        )

        print(result)


def md5_b64(filename, blocksize=65536):
    hash = hashlib.md5()
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(blocksize), b""):
            hash.update(block)
    return base64.standard_b64encode(hash.digest()).decode('ascii')


def run_build(_settings,
              _safile_settings,
              oice_id,
              ks_view_url,
              oice_communication_url,
              og_image_button_url,
              og_image_origin_url,
              email,
              isPreview,
              batchId):

    pyramid_safile.init_factory(_safile_settings)

    engine = engine_from_config(_settings)
    DBSession.configure(bind=engine)

    with transaction.manager:
        oice = OiceQuery(DBSession).get_by_id(oice_id)
        characters = CharacterQuery(DBSession).fetch_by_oice(oice)

        payload = {
            'title': oice.filename,
            'id': oice_id,
            'url': ks_view_url
        }
        if batchId:
            payload["batchId"] = batchId

        try:
            temp_folder = tempfile.mkdtemp()
            output_path = temp_folder + '/build'
            builder = KSScriptBuilder(
                _settings["o2.build_script"],
                _settings["o2.resize_script"],
                oice,
                output_path,
                ks_view_url,
                oice_communication_url,
                og_image_button_url,
                og_image_origin_url,
                characters=characters,
            )

            builder.build()

            view_path = _settings["o2.output_dir"] % {'ks_uuid': oice.uuid}

            # remove the old version
            if os.path.exists(view_path):
                shutil.rmtree(view_path)
            if not isPreview and _settings["gcloud.enable_upload"] in {'1', 'true', True}:
                client = storage.Client.from_service_account_json(
                        os.path.abspath(_settings["gcloud.json_path"]),
                        project=_settings["gcloud.project_id"]
                    )
                if client:
                    bucket = client.get_bucket(_settings["gcloud.bucket_id"])

                    for dir_, _, files in os.walk(output_path):
                        for fileName in files:
                            relDir = os.path.relpath(dir_, output_path)
                            if '.' != relDir:
                                blob_path = os.path.join('view', oice.uuid, relDir, fileName)
                            else:
                                blob_path = os.path.join('view', oice.uuid, fileName)
                            blob = bucket.get_blob(blob_path)
                            if blob:
                                md5_hash = blob.md5_hash
                                if md5_hash:
                                    if md5_b64(os.path.join(dir_, fileName)) == md5_hash:
                                        log.info('Identical md5 exist on gcloud, skipping: ' + fileName)
                                        continue
                            else:
                                blob = bucket.blob(blob_path)
                            log.info('Uploading to google cloud: ' + fileName)
                            blob.upload_from_filename(filename=os.path.join(dir_, fileName))
                            if fileName == 'script.js':
                                blob.cache_control = "private, max-age=0, no-transform"
                                blob.patch()

            if not isPreview:
                oice.story.updated_at = datetime.utcnow()

            # move the new build to folder
            shutil.move(
                output_path, _settings["o2.output_dir"] % {'ks_uuid': oice.uuid})
            shutil.rmtree(temp_folder)
        except Exception:
            if email:
                update_user_mailchimp_stage(email=email, stage=3)

            log.exception('')

            payload["message"] = str(sys.exc_info()[1])
            send_result_request('build', payload)

        else:
            if init_slack(_settings) and not isPreview and oice.is_public():
                author = oice.story.users[0]
                if not author.is_admin():
                    send_oice_publish_message_into_slack(
                        author,
                        oice,
                        ks_view_url,
                        og_image_origin_url)
            if email:
                update_user_mailchimp_stage(email=email, stage=4)

            payload["message"] = "ok"
            send_result_request('build', payload)


class KSBuildWorker(object):

    def __init__(self, oice_id, ks_view_url, oice_communication_url, og_image_button_url, og_image_origin_url):
        super().__init__()

        self.oice_id = oice_id
        self.ks_view_url = ks_view_url
        self.oice_communication_url = oice_communication_url
        self.og_image_button_url = og_image_button_url
        self.og_image_origin_url = og_image_origin_url

    def run(self, email, isPreview = False, batchId = ""):
        global settings
        global safile_settings

        redis = Redis(settings["redis.host"], settings["redis.port"], password=settings["redis.password"])
        use_connection(redis)
        q = Queue()
        result = q.enqueue(
            run_build,
            args=(
                settings,
                safile_settings,
                self.oice_id,
                self.ks_view_url,
                self.oice_communication_url,
                self.og_image_button_url,
                self.og_image_origin_url,
                email,
                isPreview,
                batchId
            ),
            timeout=600
        )


def import_oice_script(_settings, _safile_settings, user_email, job_id, oice_id, script, language):
    socket_url = 'import/' + job_id

    try:
        # Parsing
        send_result_request(socket_url, {
            'stage': 'parsing',
        })

        used_character_ids, \
        used_asset_ids, \
        used_macro_names, \
        serialized_blocks = parse_script(script)

        pyramid_safile.init_factory(_safile_settings)

        engine = engine_from_config(_settings)
        DBSession.configure(bind=engine)

        oice = OiceQuery(DBSession).get_by_id(oice_id)
        used_library_ids = set()

        send_result_request(socket_url, {
            'stage': 'validating',
        })

        # Check characters
        characters = CharacterQuery(DBSession).fetch_by_ids(used_character_ids)
        used_valid_character_ids = set(character.id for character in characters)
        invalid_character_ids = used_character_ids - used_valid_character_ids
        if len(invalid_character_ids) > 0:
            raise ScriptImportParserError('ERR_IMPORT_SCRIPT_CHARACTER_NOT_FOUND', {
                      'characterIds': str(invalid_character_ids),
                  })
        used_library_ids.update(character.library_id for character in characters)

        # Check assets
        assets = AssetQuery(DBSession).get_by_ids(used_asset_ids)
        used_valid_asset_ids = set(asset.id for asset in assets)
        invalid_asset_ids = used_asset_ids - used_valid_asset_ids
        if len(invalid_asset_ids) > 0:
            raise ScriptImportParserError('ERR_IMPORT_SCRIPT_ASSET_NOT_FOUND', {
                      'assetIds': str(invalid_asset_ids),
                  })
        used_library_ids.update(asset.library_id for asset in assets)

        # Select used library for user if needed
        user = UserQuery(DBSession).fetch_user_by_email(user_email).one()
        used_libraries = LibraryQuery(DBSession).get_librarys_by_ids(used_library_ids)
        for library in used_libraries:
            if library not in user.libraries_selected:
                if library.price < 0:
                    raise ScriptImportParserError('ERR_IMPORT_SCRIPT_LIBRARY_NOT_OWNED', {
                              'libraryId': library.id,
                              'libraryName': library.name,
                          })
                elif library not in user.libraries_purchased:
                    raise ScriptImportParserError('ERR_IMPORT_SCRIPT_LIBRARY_NOT_PURCHASED', {
                              'libraryId': library.id,
                              'libraryName': library.name,
                          })
        user.libraries_selected.extend(used_libraries)

        # Insert blocks to database
        macros = DBSession.query(Macro).filter(Macro.tagname.in_(used_macro_names)).all()
        macros_dict = dict((macro.tagname, macro) for macro in macros)

        parent_block = DBSession.query(Block) \
                                .filter(Block.oice_id == oice.id) \
                                .order_by(Block.position.desc()) \
                                .first()
        position = parent_block.position + 1 if parent_block else 0

        characters_dict = dict((character.id, character) for character in characters)

        for index, block_dict in enumerate(serialized_blocks):
            macro_name = block_dict['macro']
            macro = macros_dict[macro_name]

            block = Block(macro=macro, oice=oice, position=position + index)
            DBSession.add(block)

            ensure_block_default_value(DBSession, block, language)

            attributes = block_dict['attributes']
            if macro_name == 'characterdialog':
                character = characters_dict[attributes['character']]

                if 'name' in attributes and not character.is_generic:
                    raise ScriptImportParserError('ERR_IMPORT_SCRIPT_CHARACTER_FORBID_RENAME', {
                              'characterId': character.id,
                          })

                # set fg as the first one for character
                attributes['fg'] = next(fg.id for fg in character.fgimages)

            update_block_attributes(DBSession, block, attributes, language)

            send_result_request(socket_url, {
                'stage': 'inserting',
                'progress': float(index + 1) / len(serialized_blocks) * 100,
            })

    except ScriptImportParserError as error:
        send_result_request(socket_url, {
            'error': True,
            'key': error.key,
            'interpolation': error.interpolation,
        })
    except Exception as error:
        send_result_request(socket_url, {
            'error': True,
            'key': 'ERR_IMPORT_SCRIPT_UNKNOWN_ERROR',
            'interpolation': {
                'message': str(error),
            },
        })
    else:
        transaction.commit()
        send_result_request(socket_url, {
            'stage': 'finished',
        })

class ImportOiceWorker(object):

    def __init__(self, user_email, job_id, oice, script_file, language):
        super().__init__()

        self.user_email = user_email
        self.job_id = job_id
        self.oice = oice
        self.script_file = script_file
        self.language = language

    def run(self):
        redis = Redis(
            settings["redis.host"],
            settings["redis.port"],
            password=settings["redis.password"],
        )
        use_connection(redis)

        result = Queue().enqueue(
            import_oice_script,
            args=(
                settings,
                safile_settings,
                self.user_email,
                self.job_id,
                self.oice,
                self.script_file,
                self.language,
            ),
            timeout=600
        )


def send_result_request(path, data={}):

    host = os.environ.get('MODMOD_SOCKETIO_HOST', '127.0.0.1')
    port = os.environ.get('MODMOD_SOCKETIO_PORT', '8082')

    url = "http://%s:%s/%s" % (host, port, path)

    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    requests.post(url, data=json.dumps(data), headers=headers)

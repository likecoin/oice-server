from datetime import datetime
import io
import json
import os.path
import uuid
from pyramid.httpexceptions import HTTPFound
import pyramid_safile
from cornice import Service
from sqlalchemy.orm.exc import NoResultFound
from pyramid.httpexceptions import HTTPForbidden
from modmod.exc import ValidationError

from ..models import (
    DBSession,
    Asset,
    AssetFactory,
    AssetQuery,
    AssetType,
    CharacterQuery,
    LibraryFactory,
    LibraryQuery,
    StoryQuery,
    User,
    UserQuery,
)
from ..operations import asset as operations
from ..operations.worker import AudioFileWorker
from ..operations.image_handler import ResizeBackgroundImage

library_assets_typed = Service(name='library_assets_typed',
                               path='library/{library_id}/assets/{asset_type}',
                               renderer='json',
                               factory=LibraryFactory,
                               traverse='/{library_id}')
library_assets = Service(name='library_assets',
                         path='library/{library_id}/assets',
                         renderer='json',
                         factory=LibraryFactory,
                         traverse='/{library_id}')
story_assets = Service(name='story_assets',
                         path='story/{story_id}/assets',
                         renderer='json')
asset_download = Service(name='asset_download',
                     path='asset/{asset_id}/download',
                     renderer='json')
asset = Service(name='asset',
                path='asset/{asset_id}',
                renderer='json',
                factory=AssetFactory,
                traverse='/{asset_id}')

SUPPORT_AUDIO_FORMATS = set([
    '.m4a',
    '.mp3',
    '.wav',
])

@library_assets_typed.get()
def list_asset(request):
    email = request.authenticated_userid
    try:
        user = UserQuery(DBSession).fetch_user_by_email(email=email).one()
    except NoResultFound:
        raise HTTPForbidden

    library = request.context
    if not library.is_public:
        # check correct owner if library is not public
        if user not in library.users:
            raise HTTPForbidden

    asset_type = request.matchdict['asset_type']

    assets = AssetQuery.fetch_by_library(
        library=library,
        session=DBSession)
    return {
        'code': 200,
        'assets': [a.serialize() for a in assets if any(at.folder_name == asset_type for at in a.asset_types)]
    }


@story_assets.get(permission='get')
def list_asset(request):
    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one()

    assets = [asset.serialize() for library in user.libraries_selected \
                for asset in library.asset \
                if not asset.is_hidden or user in library.users]

    return {
        'code': 200,
        'assets': assets
    }

def validate_audio_format(extension):
    if not extension.lower() in SUPPORT_AUDIO_FORMATS:
        raise ValidationError('ERR_AUDIO_FORMAT_UNSUPPORTED')

def handle_audio_asset_files(job_id, assets, asset_files):
    audio_bytes_list = [io.BufferedReader(f.file).read() for f in asset_files]
    worker = AudioFileWorker(job_id, assets, audio_bytes_list)
    worker.run()

def create_asset(asset_types, asset_type, meta, asset_file, library_id, user_email, order):
    credits_url = meta.get('creditsUrl')

    if 'credits' in meta:
        users = UserQuery(DBSession).fetch_user_by_ids(user_ids=meta['credits'])
    else:
        users = [UserQuery(DBSession).fetch_user_by_email(email=user_email).one()]

    # Set name_en as default
    name_en = meta['nameEn'] if 'nameEn' in meta else None
    name_tw = meta['nameTw'] if 'nameTw' in meta else name_en
    name_jp = meta['nameJp'] if 'nameJp' in meta else name_en

    file_extension = os.path.splitext(asset_file.filename)[1].lower()
    # Set filename to <type><file extension>
    asset_file.filename = asset_types[0].type_ + file_extension

    handle = None
    if asset_type == 'bgm' or asset_type == 'se':
        validate_audio_format(file_extension)
    else:
        factory = pyramid_safile.get_factory()
        handle = factory.create_handle(asset_file.filename, asset_file.file)
        if asset_type == 'bgimage':
            bgImageHandler = ResizeBackgroundImage(handle.dst)
            bgImageHandler.run()

    asset = Asset.from_handle(handle=handle,
                              asset_types=asset_types,
                              name_tw=name_tw,
                              name_en=name_en,
                              name_jp=name_jp,
                              library_id=library_id,
                              filename=asset_file.filename,
                              users=users,
                              credits_url=credits_url,
                              order=order)

    return asset

@library_assets_typed.post(permission='set')
def add_asset(request):
    asset_type = request.matchdict['asset_type']
    library_id = request.context.id
    user_email = request.authenticated_userid

    try:
        asset_types = DBSession.query(AssetType) \
                               .filter(AssetType.folder_name == asset_type) \
                               .all()

        meta = json.loads(request.POST['meta'])
        asset_file = request.POST['asset'] if 'asset' in request.POST \
                        else [request.POST['asset' + str(index)] for index in range(len(meta))]
        asset_category = asset_types[0].type_

        if asset_category == 'audio':
            # only audio assets support multiple upload at this point
            return add_assets(asset_types, asset_type, meta, asset_file, library_id, user_email)
        else:
            order = 0
            if 'order' in meta:
                order = int(meta['order']) - 1
                parent_asset = DBSession.query(Asset) \
                                        .filter(Asset.order == order) \
                                        .filter(Asset.library_id == library_id) \
                                        .first() if order else None
                operations.insert_asset(DBSession, asset, parent_asset)
            else:
                order = AssetQuery(DBSession) \
                    .get_last_order_in_library(library_id=library_id)

            asset = create_asset(asset_types, asset_type, meta, asset_file, library_id, user_email, order)
            DBSession.add(asset)
            DBSession.flush()

            if 'characterId' in meta:
                character_id = meta['characterId']
                character = CharacterQuery(DBSession) \
                    .fetch_character_by_id(character_id=character_id).one()
                character.fgimages.append(asset)

            asset.library.updated_at = datetime.utcnow()
            asset.library.launched_at = datetime.utcnow()

            return {
                'code': 200,
                'message': 'ok',
                'asset': asset.serialize(),
            }
    except ValueError as e:
        raise ValidationError(str(e))

def add_assets(asset_types, asset_type, metas, asset_files, library_id, user_email):
    assets = []
    job_id = uuid.uuid4().hex

    order = AssetQuery(DBSession) \
        .get_last_order_in_library(library_id=library_id)

    for index, (asset_file, meta) in enumerate(zip(asset_files, metas)):
        new_order = order + index
        asset = create_asset(asset_types, asset_type, meta, asset_file, library_id, user_email, new_order)
        assets.append(asset)

    DBSession.flush()

    handle_audio_asset_files(job_id, assets, asset_files)

    return {
        'code': 200,
        'message': 'ok',
        'assets': [a.serialize() for a in assets],
        'jobId': job_id,
    }

@asset_download.get(permission='get')
def show_asset(request):
    asset_id = request.matchdict['asset_id']

    asset = DBSession.query(Asset) \
                     .filter(Asset.id == asset_id) \
                     .one()

    return HTTPFound(location=asset.storage.url)


@asset.get(permission='get')
def get_asset(request):
    asset = request.context
    return {
        'code': 200,
        'message': 'ok',
        'asset': asset.serialize(),
    }

@asset.post(permission='set')
def update_asset(request):
    asset = request.context
    try:
        meta = json.loads(request.POST['meta'])

        if 'credits' in meta:
            users = UserQuery(DBSession).fetch_user_by_ids(user_ids=meta['credits'])
            if users:
                asset.users = users
            else:
                asset.users = []

        if 'creditsUrl' in meta:
            asset.credits_url = meta['creditsUrl']

        if 'nameTw' in meta:
            asset.name_tw = meta['nameTw']
        if 'nameEn' in meta:
            asset.name_en = meta['nameEn']
        if 'nameJp' in meta:
            asset.name_jp = meta['nameJp']

        job_id = None
        if 'asset' in request.POST:
            asset_file = request.POST['asset']

            file_extension = os.path.splitext(asset_file.filename)[1].lower()
            # Set filename to <type><file extension>
            asset_file.filename = asset.asset_types[0].type_ + file_extension

            asset.filename = asset_file.filename

            if asset.asset_types[0].type_ == 'audio':
                job_id = uuid.uuid4().hex
                validate_audio_format(file_extension)
                handle_audio_asset_files(job_id, [asset], [asset_file])
            else:
                factory = pyramid_safile.get_factory()
                handle = factory.create_handle(asset_file.filename, asset_file.file)
                if asset.asset_types[0].folder_name == 'bgimage':
                    bgImageHandler = ResizeBackgroundImage(handle.dst)
                    bgImageHandler.run()

                asset.import_handle(handle)

            DBSession.add(asset)

        updated_asset = asset.serialize()
        if job_id:
            updated_asset['jobId'] = job_id
        else:
            asset.library.updated_at = datetime.utcnow()

        return {
            'code': 200,
            'message': 'ok',
            'asset': updated_asset,
        }
    except ValueError as e:
        raise ValidationError(str(e))

@asset.put(permission='set')
def move_asset(request):
    order = int(request.json_body.get("order", 0)) - 1
    asset = request.context
    parent_asset = None
    if order:
        parent_asset = DBSession.query(Asset) \
                                .filter(Asset.order == order) \
                                .filter(Asset.library_id == asset.library_id) \
                                .first()
    operations.move_under(asset, parent_asset, session=DBSession)

    return {
        "message": "ok",
        "asset": asset.serialize()
    }
@asset.delete(permission='set')
def delete_asset(request):
    asset = request.context

    operations.delete_asset(DBSession, asset)

    asset.library.updated_at = datetime.utcnow()

    return {
        'code': 200,
        'message': 'ok'
    }

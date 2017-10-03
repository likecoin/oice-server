from cornice import Service

import io
import os.path
import transaction
import json
import cgi
import datetime
import time
import uuid
import pyramid_safile
from pyramid.security import authenticated_userid
from pyramid.response import FileResponse
from pyramid.httpexceptions import HTTPForbidden
from modmod.exc import ValidationError
from sqlalchemy.sql.expression import false
from sqlalchemy.orm.exc import NoResultFound
from zope.sqlalchemy import mark_changed
from . import dict_get_value

from ..models import (
    DBSession,
    AssetQuery,
    AssetTypeQuery,
    FeaturedOice,
    TutorialOice,
    Oice,
    OiceFactory,
    OiceQuery,
    StoryFactory,
    LibraryFactory,
    StoryQuery,
    LibraryQuery,
    UserQuery,
    ProjectExportFactory,
    ProjectExport,
    UserReadOiceProgress,
    UserReadOiceProgressQuery,
)

from ..operations.script_validator import ScriptValidator
from ..operations.image_handler import ComposeOgImage, ComposeCoverImage
from ..operations.worker import ExportWorker, ImportOiceWorker, KSBuildWorker
from ..operations.credit import get_oice_credit
from ..operations.script_export_default import OICE_INTERACTION_SCRIPT
from ..config import (
    get_oice_view_url,
    get_oice_preview_url,
    get_oice_communication_url,
)
from . import (
    set_basic_info_oice_log,
    set_basic_info_membership_log,
    set_basic_info_log,
    set_basic_info_oice_log_author,
    check_is_language_valid,
)
from ..operations.story import fork_story as do_fork_story
from ..operations.oice import fork_oice as do_fork_oice, translate_oice
from ..operations.block import count_words_of_block
from .util import (
    update_user_mailchimp_stage,
    log_message,
)
import logging


log = logging.getLogger(__name__)
KAFKA_TOPIC_OICE = 'oice-oice'

story_id_oice = Service(name='story_id_oice',
                  path='story/{story_id}/oice',
                  renderer='json',
                  factory=StoryFactory,
                  traverse='/{story_id}')
story_id_oice_order = Service(name='story_id_oice_order',
                      path='story/{story_id}/oice/order',
                      renderer='json',
                      factory=StoryFactory,
                      traverse='/{story_id}')
oice_id = Service(name='oice_id',
                  path='oice/id/{oice_id}',
                  renderer='json',
                  factory=OiceFactory,
                  traverse='/{oice_id}')

oice_more = Service(name='oice_more',
                  path='oice/{oice_id}/more',
                  renderer='json',
                  factory=OiceFactory,
                  traverse='/{oice_id}')

oice_read = Service(name='oice_read',
                    path='oice/{oice_id}/read',
                    renderer='json',
                    factory=OiceFactory,
                    traverse='/{oice_id}')
oice_uuid_og = Service(name='oice_uuid_og',
                  path='oice/uuid/{oice_uuid}',
                  renderer='json')

oice_validate = Service(name='oice_validate',
                      path='story/{story_id}/oice/{oice_id}/validate',
                      renderer='json',
                      factory=OiceFactory,
                      traverse='/{oice_id}')

oice_import = Service(name='oice_import',
                    path='oice/{oice_id}/import',
                    renderer='json',
                    factory=OiceFactory,
                    traverse='/{oice_id}')

oice_export = Service(name='oice_export',
                    path='story/{story_id}/oice/{oice_id}/export',
                    renderer='json',
                    factory=OiceFactory,
                    traverse='/{oice_id}')

oice_download = Service(name='oice_download',
                           path='oice/{oice_id}/export/' +
                           '{project_export_id}',
                           renderer='json',
                           factory=ProjectExportFactory,
                           traverse='/{project_export_id}')
oice_build = Service(name='oice_build',
                   path='oice/{oice_id}/build',
                   renderer='json',
                   factory=OiceFactory,
                   traverse='/{oice_id}')
oice_build_all = Service(name='oice_build_all',
                       path='oice/buildall',
                       renderer='json')
oice_preview = Service(name='oice_preview',
                   path='oice/{oice_id}/preview',
                   renderer='json',
                   factory=OiceFactory,
                   traverse='/{oice_id}')
oice_fork = Service(name='oice_fork',
                   path='oice/{oice_id}/fork',
                   renderer='json',
                   factory=OiceFactory,
                   traverse='/{oice_id}')
oice_copy = Service(name='oice_copy',
                    path='oice/{oice_id}/copy',
                    renderer='json',
                    factory=OiceFactory,
                    traverse='/{oice_id}')
oice_credits = Service(name='oice_credits',
                    path='credits/oice/{oice_id}',
                    renderer='json',
                    factory=OiceFactory,
                    traverse='/{oice_id}')
oice_featured = Service(name='oice_featured',
                    path='oice/featured',
                    renderer='json')
oice_tutorial = Service(name='oice_tutorial',
                    path='oice/tutorial',
                    renderer='json')
story_id_oice_profile = Service(name='story_id_oice_profile',
                    path='user/{user_id}/story/{story_id}',
                    renderer='json',
                    factory=StoryFactory,
                    traverse='/{story_id}')
oice_view_count = Service(name='oice_view_count',
                    path='oice/{oice_id}/viewCount',
                    renderer='json',
                    factory=OiceFactory,
                    traverse='/{oice_id}')
oice_id_wordcount = Service(name='oice_id_wordcount',
                            path='oice/{oice_id}/wordcount',
                            renderer='json',
                            factory=OiceFactory,
                            traverse='/{oice_id}')
oice_communication = Service(name='oice_communication',
                    path='oice/communication',
                    renderer='json')
oice_translate = Service(name='oice_translate',
                        path='oice/{oice_id}/translate',
                        renderer='json',
                        factory=OiceFactory,
                        traverse='/{oice_id}')


def fetch_oice_query_language(request, oice):
    query_language = request.params.get('language')
    return check_is_language_valid(query_language) if query_language else oice.story.language


@story_id_oice.get(permission='get')
def list_oice(request):
    # Obtain for story properties
    request_story_id = request.matchdict['story_id']

    # Query for oice file list
    oice_list = OiceQuery(DBSession) \
        .fetch_oice_list_by_id(story_id=request_story_id)

    return {
        'oices': [oice.serialize(language=fetch_oice_query_language(request, oice)) for oice in oice_list],
        'code': 200,
        'message': 'ok'
    }


@story_id_oice.post(permission='set')
def add_oice(request):
    email = authenticated_userid(request)
    update_user_mailchimp_stage(email=email, stage=2)
    user = UserQuery(DBSession).fetch_user_by_email(email=email).one()

    story_id = request.matchdict['story_id']

    story = StoryQuery(DBSession).get_story_by_id(story_id)

    episode_number = len(story.oice) + 1

    oice_name = 'Episode {}'
    if story.language[:2] == 'zh':
        oice_name = '第{}回'
    elif story.language[:2] == 'ja':
        oice_name = 'エピソード {}'

    oice_name = oice_name.format(episode_number)

    new_oice = Oice(story_id=story_id, \
        filename=oice_name, \
        language=story.language, \
        order=len(story.oice))

    DBSession.add(new_oice)
    DBSession.flush()

    log_dict = {
        'action': 'createOice',
        'description': new_oice.og_description,
        'order': new_oice.order,
        'updatedAt': new_oice.updated_at.isoformat(),
        'language': new_oice.language,
        'isShowAd': new_oice.is_show_ad,
    }
    log_dict = set_basic_info_oice_log(user, new_oice, log_dict)
    log_dict = set_basic_info_log(request, log_dict)
    log_message(KAFKA_TOPIC_OICE, log_dict)

    return {
        'oice': new_oice.serialize(language=fetch_oice_query_language(request, new_oice)),
        'code': 200,
        'message': 'ok'
    }


@story_id_oice_order.post(permission='get')
def update_oice_order(request):
    oice_to_be_updated = request.json_body
    log_dict = {
        'newOrder': [],
        'action': 'changeOrder',
    }
    for index, a in enumerate(oice_to_be_updated):
        oice_id = a['id']
        oice = OiceQuery(DBSession) \
            .get_by_id(oice_id)
        oice.order = index;
        log_dict['newOrder'].append({
                'oiceId': oice_id,
                'order': index
            })

    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one()
    log_dict = set_basic_info_oice_log(user, oice, log_dict)
    log_dict = set_basic_info_log(request, log_dict)
    log_message(KAFKA_TOPIC_OICE, log_dict)
    return {
        'code': 200,
        'message': 'ok'
    }


@oice_uuid_og.get()
def get_og(request):
    oice_uuid = request.matchdict['oice_uuid']
    oice = OiceQuery(DBSession).get_by_uuid(uuid=oice_uuid)
    if not oice:
        raise ValidationError('ERR_OICE_NOT_FOUND')

    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one_or_none()

    return {
        'oice': oice.serialize(user, language=fetch_oice_query_language(request, oice)),
        'code': 200,
        'message': 'ok'
    }


@oice_id.get()
def get_oice(request):
    oice = request.context

    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one_or_none()

    return {
        'oice': oice.serialize(user, language=fetch_oice_query_language(request, oice)),
        'code': 200,
        'message': 'ok'
    }


@oice_id.post(permission='get')
def update_oice(request):
    oice_id = request.matchdict['oice_id']

    oice = OiceQuery(DBSession).get_by_id(oice_id=oice_id)
    query_language = fetch_oice_query_language(request, oice)

    try:
        log_dict = {
            'change': [],
            'action': 'changeSetting',
        }
        if 'meta' in request.POST:
            meta = json.loads(request.POST['meta'])

            if 'name' in meta:
                old_value = oice.filename
                new_value = meta['name']
                if old_value != new_value:
                    log_dict['change'].append({
                        'whichFieldChange': 'oice',
                        'beforeChange': old_value,
                        'afterChange': new_value,
                    })
                    oice.set_name(new_value, query_language)

            if 'sharingOption' in meta and query_language == oice.story.language:
                old_value = oice.sharing_option
                new_value = meta['sharingOption']
                if old_value != new_value:
                    log_dict['change'].append({
                        'whichFieldChange': 'sharingOption',
                        'beforeChange': old_value,
                        'afterChange': new_value,
                    })
                    oice.sharing_option = new_value

            if 'isShowAd' in meta:
                old_value = oice.is_show_ad
                new_value = meta['isShowAd']
                if old_value != new_value:
                    log_dict['change'].append({
                        'whichFieldChange': 'isShowAd',
                        'beforeChange': old_value,
                        'afterChange': new_value,
                    })
                    oice.is_show_ad = new_value

        DBSession.add(oice)
        DBSession.flush()

        user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one()
        log_dict = set_basic_info_oice_log(user, oice, log_dict)
        log_dict = set_basic_info_log(request, log_dict)
        log_message(KAFKA_TOPIC_OICE, log_dict)
    except ValueError as e:
        raise ValidationError('Request object is invalid')
    else:
        return {
            'oice': oice.serialize(language=query_language),
            'code': 200,
            'message': 'ok'
        }


@oice_id.delete(permission='set')
def delete_oice(request):
    oice = request.context

    oice.is_deleted = True
    DBSession.query(Oice) \
           .filter(
                Oice.story_id == oice.story_id,
                Oice.order > oice.order
            ) \
           .update(
                {Oice.order: Oice.order-1}
            )

    log_dict = {
        'action': 'deleteOice',
    }
    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one()
    log_dict = set_basic_info_oice_log(user, oice, log_dict)
    log_dict = set_basic_info_log(request, log_dict)
    log_message(KAFKA_TOPIC_OICE, log_dict)
    return {
        'code': 200,
        'message': 'ok'
    }


@oice_more.get()
def get_more_info(request):
    oice = request.context
    story = oice.story

    # sort story's oices according to order
    oices = sorted(story.oice, key=lambda o: o.order)
    # place oice with larger order than oice.order at the back
    episode = next(i for (i, o) in enumerate(oices) if o.id == oice.id) + 1
    oices = oices[episode:] + oices[:episode - 1]

    return {
        'code': 200,
        'oices': [o.serialize(fetch_oice_query_language(request, o)) for o in oices \
                  if not o.is_deleted and o.is_public()],
    }


@oice_read.post()
def set_oice_progress(request):
    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one_or_none()
    if not user:
        raise HTTPForbidden

    oice = request.context

    progress = UserReadOiceProgressQuery(DBSession).fetch_by_user_id_and_oice_id(user.id, oice.id)
    if not progress:
        session = DBSession()
        session.execute("UPDATE oice SET view_count = view_count + 1 WHERE id = %d" % oice.id)
        mark_changed(session)
        session.flush()

        progress = UserReadOiceProgress(user_id=user.id, oice_id=oice.id)

    progress.is_finished = request.json_body.get('isFinished', False)
    progress.updated_at = datetime.datetime.utcnow()  # Force update the update_at even no value changes

    log_dict = {
        'action'     : 'readOice' if progress.is_finished else 'viewOice',
        'description': oice.og_description,
        'order'      : oice.order,
        'updatedAt'  : oice.updated_at.isoformat(),
        'language'   : oice.language,
        'isShowAd'   : oice.is_show_ad,
        'referrer'   : dict_get_value(request.json_body, ['referrer'], 'none'),
        'channel'    : dict_get_value(request.json_body, ['channel'], 'direct'),
    }
    log_dict = set_basic_info_membership_log(user, log_dict)
    log_dict = set_basic_info_oice_log_author(oice.story.users[0], oice, log_dict)
    log_dict = set_basic_info_log(request, log_dict)
    log_message(KAFKA_TOPIC_OICE, log_dict)

    DBSession.add(progress)

    return {
        'code': 200,
        'message': 'ok',
    }


@oice_validate.get(permission='get')
def validate_oice(request):

    oice = request.context

    validator = ScriptValidator(oice=oice)
    return {
        'code': 200,
        'errors': validator.get_errors(),
    }


@oice_import.post(permission='set')
def import_oice(request):

    oice = request.context

    if 'script' not in request.POST:
        raise ValidationError('ERR_IMPORT_SCRIPT_FILE_NOT_FOUND')

    user_email = request.authenticated_userid
    oice_id = request.matchdict['oice_id']
    script = request.POST['script']
    job_id = uuid.uuid4().hex
    language = fetch_oice_query_language(request, oice)

    try:
        text_wrapper = io.TextIOWrapper(script.file, encoding='utf-8-sig')
        script_text = text_wrapper.read()
        # handle Windows text file
        script_text = script_text.replace('\r', '')
    except Exception as error:
        raise ValidationError('ERR_IMPORT_SCRIPT_FILE_CANNOT_OPEN')

    worker = ImportOiceWorker(user_email, job_id, oice_id, script_text, language)
    worker.run()

    return {
        'code': 200,
        'jobId': job_id,
    }


@oice_export.get(permission='get')
def export_ks(request):

    story_id = request.matchdict['story_id']

    story = StoryQuery(DBSession)\
        .get_story_by_id(story_id)
    oice = request.context

    project_export = ProjectExport(story=story, oice=oice)
    DBSession.add(project_export)
    DBSession.flush()

    project_export_id = project_export.id

    # explicitly commit the transaction,
    # because we want to make sure the worker can find it from DB
    transaction.commit()

    worker = ExportWorker(project_export_id)
    worker.run()

    return {
        'message': 'ok',
        'id': project_export_id
    }


@oice_build.get()
def build_oice(request):

    oice_id = request.matchdict["oice_id"]
    oice = OiceQuery(DBSession).get_by_id(oice_id=oice_id)

    email = authenticated_userid(request)

    view_url = get_oice_view_url(oice.uuid)
    oice_communication_url = get_oice_communication_url()
    og_image_button_url = oice.og_image_url_obj.get('button', '')
    og_image_origin_url = oice.image_url_obj.get('origin', '')
    worker = KSBuildWorker(oice.id, view_url, oice_communication_url, og_image_button_url, og_image_origin_url)
    worker.run(email=email)
    oice.publish()

    log_dict = {
        'action': 'publishOice',
        'url': view_url,
    }
    user = UserQuery(DBSession).fetch_user_by_email(email=email).one()
    log_dict = set_basic_info_oice_log(user, oice, log_dict)
    log_dict = set_basic_info_log(request, log_dict)
    log_message(KAFKA_TOPIC_OICE, log_dict)
    return {
        'message': 'ok',
        'view_url': view_url
    }


@oice_build_all.get(permission='admin_set')
def build_all_oice(request):
    oices = DBSession.query(Oice) \
            .filter(Oice.sharing_option == 0) \
            .all()

    batchId = uuid.uuid4().hex

    for oice in oices:
        view_url = get_oice_view_url(oice.uuid)
        oice_communication_url = get_oice_communication_url()
        og_image_button_url = oice.og_image_url_obj.get('button', '')
        og_image_origin_url = oice.image_url_obj.get('origin', '')
        worker = KSBuildWorker(oice.id, view_url, oice_communication_url, og_image_button_url, og_image_origin_url)
        worker.run(email="", isPreview=False, batchId=batchId)
    return {
        'message': 'ok',
        'batchId': batchId,
        'jobCount': len(oices)
    }


@oice_preview.get()
def preview_oice(request):

    oice_id = request.matchdict["oice_id"]
    oice = OiceQuery(DBSession).get_by_id(oice_id=oice_id)

    email = authenticated_userid(request)

    view_url = get_oice_preview_url(oice.uuid)
    oice_communication_url = get_oice_communication_url()
    og_image_button_url = oice.og_image_url_obj.get('button', '')
    og_image_origin_url = oice.image_url_obj.get('origin', '')
    worker = KSBuildWorker(oice.id, view_url, oice_communication_url, og_image_button_url, og_image_origin_url)
    worker.run(email=email, isPreview=True)
    oice.preview()

    log_dict = {
        'action': 'previewOice',
        'url': view_url,
    }
    user = UserQuery(DBSession).fetch_user_by_email(email=email).one()
    log_dict = set_basic_info_oice_log(user, oice, log_dict)
    log_dict = set_basic_info_log(request, log_dict)
    log_message(KAFKA_TOPIC_OICE, log_dict)
    return {
        'message': 'ok',
        'view_url': view_url
    }


@oice_fork.post()
def fork_oice(request):

    oice = request.context
    story_id = oice.story_id
    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one()
    if not user:
        raise HTTPForbidden

    story = oice.story
    forked_story = next((user_story for user_story in user.stories if story_id == user_story.fork_of), None)
    fork_serial_number = 0
    if not forked_story:
        is_self_forking = story in user.stories
        forked_story = do_fork_story(DBSession, story, is_self_forking)
        forked_story.users = [user]
    else:
        fork_serial_number = sum(1 for o in forked_story.oice if oice.id == o.fork_of)
    new_oice = do_fork_oice(DBSession, forked_story, oice, fork_serial_number)

    log_dict = {
        'action': 'forkOice',
        'oiceForkOf': new_oice.fork_of,
        'description': new_oice.og_description,
        'order': new_oice.order,
        'updatedAt': new_oice.updated_at.isoformat(),
        'language': new_oice.language,
        'isShowAd': new_oice.is_show_ad,
    }
    log_dict = set_basic_info_oice_log(user, new_oice, log_dict)
    log_dict = set_basic_info_log(request, log_dict)
    log_message(KAFKA_TOPIC_OICE, log_dict)
    return {
        'message': 'ok',
        'oice': new_oice.serialize(language=fetch_oice_query_language(request, oice))
    }


@oice_copy.post(permission='set')
def copy_oice(request):
    oice = request.context
    story_id = oice.story_id
    try:
        if 'storyId' in request.json_body:
            story_id = int(request.json_body['storyId'])
    except Exception:
      pass

    story = StoryQuery(DBSession).get_story_by_id(story_id)
    fork_serial_number = sum(1 for o in story.oice if oice.id == o.fork_of)
    new_oice = do_fork_oice(DBSession, story, oice, fork_serial_number)

    log_dict = {
        'action': 'copyOice',
        'oiceForkOf': new_oice.fork_of,
    }
    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one()
    log_dict = set_basic_info_oice_log(user, new_oice, log_dict)
    log_dict = set_basic_info_log(request, log_dict)
    log_message(KAFKA_TOPIC_OICE, log_dict)
    return {
        'message': 'ok',
        'oice': new_oice.serialize(language=fetch_oice_query_language(request, oice))
    }


@oice_download.get(permission='get')
def download_oice(request):

    project_export = request.context
    response = FileResponse(project_export.exported_files.dst,
                            request=request,
                            content_type='application/zip')
    ts = time.time()
    currentTime = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d_%H%M%S')
    fileName = currentTime + '.zip'
    response.headers['Content-Disposition'] = \
        'attachment; filename="%s"' % fileName
    return response


@oice_credits.get()
def get_oice_credits(request):
    oice = request.context
    credits = get_oice_credit(oice)

    return {
        'message': 'ok',
        'code': 200,
        'credits': credits,
    }


@oice_featured.get()
def get_featured_oice(request):

    featured_oices = DBSession.query(FeaturedOice) \
                                    .order_by(FeaturedOice.order) \
                                    .all()

    return {
        'code': 200,
        'message': 'ok',
        'featuredOices': [o.oice.serialize() for o in featured_oices]
    }


@oice_tutorial.get()
def get_tutorial_oice(request):

    tutorial_oices = DBSession.query(TutorialOice) \
                                    .order_by(TutorialOice.order) \
                                    .all()

    return {
        'code': 200,
        'message': 'ok',
        'oices': [o.oice.serialize(language=fetch_oice_query_language(request, o)) for o in tutorial_oices]
    }


@story_id_oice_profile.get()
def list_oice_profile(request):
    # Obtain for story properties
    request_story_id = request.matchdict['story_id']

    # Query for oice file list
    oice_list = OiceQuery(DBSession) \
            .fetch_oice_list_by_id(story_id=request_story_id) \
            .filter(Oice.sharing_option == 0)
    oice_list = [o.serialize_profile(fetch_oice_query_language(request, o)) for o in oice_list]

    return {
        "code": 200,
        "message": "ok",
        "oices": oice_list,
    }


@oice_view_count.post()
def increment_oice_view_count(request):
    request_oice_id = request.matchdict['oice_id']
    session = DBSession()
    session.execute("UPDATE oice SET view_count = view_count + 1 WHERE id = " + request_oice_id)
    mark_changed(session)
    session.flush()

    oice = OiceQuery(DBSession).get_by_id(oice_id=request_oice_id)
    viewer = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one_or_none()
    log_dict = {
        'action'            : 'viewOice',
        'description'       : oice.og_description,
        'order'             : oice.order,
        'updatedAt'         : oice.updated_at.isoformat(),
        'language'          : oice.language,
        'isShowAd'          : oice.is_show_ad,
    }
    log_dict = set_basic_info_membership_log(viewer, log_dict)
    log_dict = set_basic_info_oice_log_author(oice.story.users[0], oice, log_dict)
    log_dict = set_basic_info_log(request, log_dict)
    log_message(KAFKA_TOPIC_OICE, log_dict)

    return {
        "code": 200,
        "message": "ok",
    }


@oice_id_wordcount.get(permission='get')
def get_word_count_of_oice(request):
    oice = request.context
    query_language = fetch_oice_query_language(request, oice)

    return {
        "code": 200,
        "message": "ok",
        "wordcount": count_words_of_block(DBSession, oice=oice, language=query_language),
    }


@oice_communication.get()
def communicate(request):
    result = {};

    communicate_type = request.GET.get('type')
    if communicate_type == 'interaction':
        result['script'] = OICE_INTERACTION_SCRIPT

    return {
        "code": 200,
        "message": "ok",
        "result": result,
    }


@oice_translate.post(permission='get')
def post_translate(request):
    oice = request.context
    source_language = check_is_language_valid(request.json_body.get("sourceLanguage", None))
    target_language = check_is_language_valid(request.json_body.get("targetLanguage", None))
    if not target_language:
        raise ValidationError("ERR_INVALID_TARGET_LANGUAGE")
    translate_oice(oice, target_language, source_language)

    return {
        "code": 200,
        "message": "ok",
        "oice": oice.serialize(language=target_language),
    }

from sqlalchemy.orm.session import make_transient
import pyramid_safile
import logging
from google.cloud import translate
from modmod.exc import ValidationError
from ..models import (
    StoryQuery
)
from ..config import get_gcloud_json_path, get_gcloud_project_id
from .oice import translate_oice
from ..views.util import get_language_code_for_translate


log = logging.getLogger(__name__)

def fork_story(session, story, is_self_forking=False):
    handle = None
    if story.cover_storage:
        try:
            cover_storage = story.cover_storage
            factory = pyramid_safile.get_factory()
            handle = factory.create_handle(cover_storage.filename, open(cover_storage.dst, 'rb'))
        except FileNotFoundError as e:
            log.error(str(e))

    og_image_handle = None
    if story.og_image:
        try:
            og_image = story.og_image
            factory = pyramid_safile.get_factory()
            og_image_handle = factory.create_handle(og_image.filename, open(og_image.dst, 'rb'))
        except FileNotFoundError as e:
            log.error(str(e))

    session.expunge(story)
    original_story = StoryQuery(session).get_story_by_id(story.id)
    story.fork_of = story.id
    story.id = None
    if is_self_forking:
        story.name = story.name + '(1)'
    story.import_handle(handle)
    make_transient(story)
    session.add(story)
    story.libraries = original_story.libraries
    story.localizations = original_story.localizations
    session.flush()
    return story


def remove_story_localization(session, story, language):
    if story.is_supported_language(language):
        session.delete(story.localizations[language])
        for o in story.oice:
            if language in o.localizations:
                session.delete(o.localizations[language])
            for b in o.blocks:
                for attribute in b.attributes:
                    if attribute.attribute_definition.localizable and attribute.language == language:
                        session.delete(attribute)
        session.flush()
    else:
        raise ValueError('ERR_LANGUAGE_NOT_EXIST_IN_STORY')


def translate_story(story, target_language, source_language=None, translated_story={}, translated_oices=[], client=None):
    if client is None:
        client = translate.Client.from_service_account_json(
            get_gcloud_json_path()
        )
    if not source_language:
        source_language = story.language

    target_language_code = get_language_code_for_translate(target_language)

    story.set_name(translated_story['name'], target_language)
    story.set_description(translated_story['description'], target_language)

    for o in story.oice:
        translated_oice_name = next((oice['name'] for oice in translated_oices if oice['id'] == o.id), None)
        translate_oice(o, target_language, source_language, translated_oice_name, client)


def translate_story_preview(story, target_language, source_language=None, client=None):
    if client is None:
        client = translate.Client.from_service_account_json(
            get_gcloud_json_path()
        )
    if not source_language:
        source_language = story.language

    target_language_code = get_language_code_for_translate(target_language)

    story_text_list = [story.get_name(source_language), story.get_description(source_language)]
    story_results = client.translate(story_text_list, target_language=target_language_code, model=translate.NMT)

    oices = story.oice
    oice_text_list = [oice.get_name(source_language) for oice in oices]
    oice_results = client.translate(oice_text_list, target_language=target_language_code, model=translate.NMT)
    return {
        'story': {
            'id': story.id,
            'name': story_results[0]['translatedText'],
            'description': story_results[1]['translatedText'],
        },
        'oices': [{ 'id': oices[i].id, 'name': result['translatedText'] } for i, result in enumerate(oice_results)],
    }

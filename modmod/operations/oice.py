import html
import json
import logging
import uuid

from google.cloud import translate
from sqlalchemy.orm.session import make_transient
from .block import fork_blocks, update_block_attributes
from ..models import DBSession
from ..config import get_gcloud_json_path
from ..views.util import get_language_code_for_translate


log = logging.getLogger(__name__)


def fork_oice(session, new_story, oice, serial_number=0):
    blocks = oice.blocks if oice.blocks else None
    localizations = oice.localizations if oice.localizations else None

    session.expunge(oice)
    oice.reset_state()
    oice.set_private()
    oice.fork_of = oice.id
    oice.id = None
    oice.uuid = uuid.uuid4().hex
    oice.order = len(new_story.oice)
    oice.story_id = new_story.id
    if serial_number > 0:
        oice.filename = oice.filename + '({})'.format(serial_number)

    make_transient(oice)
    session.add(oice)
    oice.story = new_story
    if localizations:
        oice.localizations = localizations
    session.flush()

    if blocks:
        fork_blocks(session, oice, blocks)

    return oice


def translate_oice(oice, target_language, source_language=None, oice_name=None, client=None):
    if client is None:
        client = translate.Client.from_service_account_json(get_gcloud_json_path())

    if not source_language:
        source_language = oice.story.language

    target_language_code = get_language_code_for_translate(target_language)

    def _translate(values):
        return client.translate(values, target_language=target_language_code, model=translate.NMT)

    if not oice_name:
        result = _translate(oice.get_name(source_language))
        oice_name = result['translatedText']
    oice.set_name(oice_name, target_language)

    block_list = []
    attr_list = []
    text_list = []
    length = 0

    def _translate_blocks():
        _results = _translate(text_list)

        for (_r, (_attrs, _name)) in zip(_results, attr_list):
            _attrs[_name] = html.unescape(_r['translatedText'])

        for (_b, _attrs) in block_list:
            update_block_attributes(DBSession, _b, _attrs, target_language)

    for b in oice.blocks:
        attrs = b.get_localizable_attributes(source_language)
        block_list.append((b, attrs))

        for name, value in attrs.items():
            if b.macro.tagname == 'option' and name == 'answers':
                # Handle for option answers
                try:
                    answers = json.loads(value)
                    answer_text_list = [answer['content'] for answer in answers]

                    results = _translate(answer_text_list)
                    for i, r in enumerate(results):
                        answers[i]['content'] = html.unescape(r['translatedText'])

                    attrs[name] = json.dumps(answers, ensure_ascii=False)
                except (AttributeError, KeyError, ValueError):
                    pass
            else:
                attr_list.append((attrs, name))
                text_list.append(value)
                length += len(value)

        if length > 256:
            _translate_blocks()

            # Reset
            block_list = []
            attr_list = []
            text_list = []
            length = 0

    if text_list:
        _translate_blocks()

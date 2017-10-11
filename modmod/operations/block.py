# pylama:ignore=E711,ignore=C901
# Need to use == None because sqlalchemy overrided the == operator
from sqlalchemy.orm.session import make_transient
from zope.sqlalchemy import mark_changed
from google.cloud import translate
import logging
from ..models import (
    DBSession,
    Attribute,
    Block,
)
from ..config import get_gcloud_json_path, get_gcloud_project_id


log = logging.getLogger(__name__)


def insert_block(session, block_to_insert, parent_block):

    """

        with the following custom queries, the modle objects cached by
        sqlalchemy will not be updated even after a transaction.

        To verify the changes are actually made, do another query and
        sqlalchemy will return the group of model objects with updated
        properties.

    """

    if parent_block:
        insert_index = parent_block.position+1
    else:
        insert_index = 0

    session.query(Block) \
           .filter(
                Block.oice == block_to_insert.oice,
                Block.position >= insert_index
            ) \
           .update(
                {Block.position: Block.position+1}
            )

    block_to_insert.position = insert_index
    session.add(block_to_insert)


def move_under(block, new_parent_block, session=DBSession):

    new_index = 0
    if new_parent_block:
        new_index = new_parent_block.position+1

        if block.oice != new_parent_block.oice:
            raise Exception('Source block and parent block are not in the same KS file')

    if block.position > new_index:
        move_up(block, new_index, session)
    elif block.position < new_index:

        # because the original block is removed, so need to -1
        new_index -= 1
        move_down(block, new_index, session)


def move_up(block, new_index, session=DBSession):

    if block.position < new_index:
        raise 'Cannot move up, direction is not correct'
    elif block.position == new_index:
        return

    session.query(Block) \
           .filter(
                Block.oice_id == block.oice_id,
                Block.position >= new_index,
                Block.position < block.position
            ) \
           .update(
                {Block.position: Block.position+1}
            )

    block.position = new_index


def move_down(block, new_index, session=DBSession):

    if block.position > new_index:
        raise 'Cannot move down, direction is not correct'
    elif block.position == new_index:
        return

    session.query(Block) \
           .filter(
                Block.oice_id == block.oice_id,
                Block.position > block.position,
                Block.position <= new_index
            ) \
           .update(
                {Block.position: Block.position-1}
            )

    block.position = new_index


def delete_block(session, block):

    session.query(Block) \
           .filter(
                Block.oice_id == block.oice_id,
                Block.position > block.position
            ) \
           .update(
                {Block.position: Block.position-1}
            )

    DBSession.delete(block)


def update_block_attributes(session, block, attributes, language):
    attr_defs = {}
    for attr_def in block.macro.attribute_definitions:
        attr_defs[attr_def.attribute_name] = attr_def

    attrs = {}
    for a in block.attributes:
        if not a.attribute_definition.localizable or a.language == language:
            attrs[a.attribute_definition.attribute_name] = a

    for (key, value) in attributes.items():
        if key == "parentId" or key == "macroId" or key not in attr_defs:
            # not a valid attribute name
            continue

        is_asset = attr_defs[key].is_asset

        if key in attrs:
            # modfiy existing attribute
            attr = attrs[key]
            if is_asset and value:
                attr.asset_id = value
            else:
                attr.value = value
            session.add(attr)

        else:
            # make new attribute
            attr_to_be_add = None
            attr_language = None
            if attr_defs[key].localizable:
                attr_language = language
            if is_asset:
                attr_to_be_add = Attribute(
                    attribute_definition=attr_defs[key],
                    block=block,
                    asset_id=value,
                    language=attr_language
                )
            else:
                attr_to_be_add = Attribute(
                    attribute_definition=attr_defs[key],
                    block=block,
                    value=value,
                    language=attr_language
                )
            session.add(attr_to_be_add)


def ensure_block_default_value(session, block, language):

    attrs = {}
    for a in block.attributes:
        attrs[a.attribute_definition.attribute_name] = a

    for attr_def in block.macro.attribute_definitions:
        attr_language = language if attr_def.localizable else None
        if attr_def.default_value is not None and attr_def.attribute_name not in attrs:
            attr = Attribute(
                attribute_definition=attr_def,
                block=block,
                value=attr_def.default_value,
                language=attr_language)
            session.add(attr)


def fork_blocks(DBSession, oice, blocks):
    batch_attributes = []
    block_id_pos_dict = {}
    new_block_pos_dict = {}
    new_oice_id = oice.id
    for block in blocks:
        attributes = block.attributes
        DBSession.expunge(block)
        block_id_pos_dict[block.id] = block.position
        block.id = None
        block.oice_id = new_oice_id
        make_transient(block)
        if attributes:
            batch_attributes.extend(attributes)
            # handle attributes in batch for better performance
            # fork_attributes(DBSession, block, attributes)
    batch_attributes.sort(key=lambda attr: attr.asset_id is None)
    session = DBSession()
    session.bulk_save_objects(blocks)
    new_blocks = DBSession.query(Block) \
        .filter(Block.oice_id == new_oice_id) \
        .order_by(Block.position) \
        .all()
    for block in new_blocks:
        new_block_pos_dict[block.position] = block
    for attr in batch_attributes:
        make_transient(attr)
        attr.id = None
        attr.block_id = new_block_pos_dict[block_id_pos_dict[attr.block_id]].id
    session.bulk_save_objects(batch_attributes)
    mark_changed(session)
    return blocks


def count_words_of_block(session, story=None, oice=None, language=None):
    if not language:
        language = story.language if story else oice.language

    sql = '''
    SELECT
        SUM(BlockWordCount.count)
    FROM (
             SELECT
                A.`block_id` AS block_id,
                CHAR_LENGTH(
                    IF(
                        M.`tagname` = 'option' AND AD.`attribute_name` = 'answers',
                        REPLACE(TRIM(LEADING '["' FROM TRIM(TRAILING '"]' FROM A.`value`->'$[*].content')), '", "', ''),
                        A.`value`
                    )
                ) AS count
            FROM
                `attribute` AS A
                JOIN `attribute_definition` AD
                    ON A.`attribute_definition_id` = AD.`id`
                JOIN `macro` M
                    ON AD.`macro_id` = M.`id`
            WHERE
                (
                    A.`language` = '%s'
                    AND
                    (
                        (
                            M.`tagname` = 'characterdialog'
                            AND AD.`attribute_name` = 'dialog'
                        )
                        OR (
                            M.`tagname` = 'addTalk'
                            AND AD.`attribute_name` = 'talk'
                        )
                        OR (
                            M.`tagname` = 'aside'
                            AND AD.`attribute_name` = 'text'
                        )
                        OR (
                            M.`tagname` = 'option'
                            AND (
                                AD.`attribute_name` = 'question'
                                OR AD.`attribute_name` = 'answers'
                            )
                        )
                    )
                )
        ) BlockWordCount
        JOIN `block` B
            ON BlockWordCount.`block_id` = B.`id`
    ''' % language

    if story:
        sql += '''
            JOIN `oice` O
                ON B.`oice_id` = O.`id`
        WHERE O.`story_id` = %d
            AND O.`is_deleted` = false
        ''' % story.id

    elif oice:
        sql += '''WHERE B.`oice_id` = %d''' % oice.id

    else:
        return 0

    result = session.execute(sql).scalar()

    return int(result) if result else 0


def translate_block(block, target_language, source_language=None, client=None):
    if client is None:
        client = translate.Client.from_service_account_json(
            get_gcloud_json_path()
        )
    target_language_code = target_language.lower()[:2]

    if not source_language:
        source_language = block.oice.story.language

    attr_list = []
    text_list = []
    attrs = block.get_localizable_attributes(source_language)
    for name, a in attrs.items():
        attr_list.append((attrs, name))
        text_list.append(a)

    if text_list:
        results = client.translate(text_list, target_language=target_language_code, model=translate.NMT)
        for (r, (a, name)) in zip(results, attr_list):
            a[name] = r['translatedText']

        update_block_attributes(DBSession, block, attrs, target_language)

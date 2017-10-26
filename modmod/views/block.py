import logging
from cornice import Service
from modmod.exc import ValidationError

from ..models import (
    DBSession,
    Macro,
    OiceFactory,
    Block,
    BlockFactory,
)

from . import log_block_message, check_is_language_valid
from . import set_basic_info_log
from ..operations import block as operations


log = logging.getLogger(__name__)

block_list = \
    Service(name='block_list',
        path='oice/{oice_id}/blocks',
        renderer='json',
        factory=OiceFactory,
        traverse='/{oice_id}')
block = \
    Service(name='block',
        path='block/{block_id}',
        renderer='json',
        factory=BlockFactory,
        traverse='/{block_id}')
blocks = \
    Service(name='blocks',
        path='blocks',
        renderer='json')
block_translate = \
    Service(name='block_translate',
        path='block/{block_id}/translate',
        renderer='json',
        factory=BlockFactory,
        traverse='/{block_id}')


@block_list.get(permission='get')
def read_blocks(request):
    request_oice_id = request.matchdict['oice_id']
    count = request.params.get("count", 2500)
    min_block_id = request.params.get("minBlockId")
    query_language = request.params.get('language')

    first_block = None

    if min_block_id is not None:
        first_block = DBSession.query(Block.position) \
            .filter(
                Block.oice_id == request_oice_id,
                Block.id >= min_block_id) \
            .order_by(Block.position) \
            .first()
    else:
        first_block = DBSession.query(Block.position) \
            .filter(Block.oice_id == request_oice_id) \
            .order_by(Block.position) \
            .first()

    if first_block is None:
        return {
            "code": 200,
            "blocks": []
        }

    blocks = DBSession.query(Block) \
        .filter(Block.oice_id == request_oice_id) \
        .filter(Block.position >= first_block.position) \
        .order_by(Block.position) \
        .limit(count) \
        .all()

    last_id = 0
    serialized = []
    for block in blocks:
        query_language = check_is_language_valid(query_language) if query_language else block.oice.story.language
        this_hash = block.serialize(query_language)
        this_hash['parentId'] = last_id
        serialized.append(this_hash)
        last_id = block.id

    return {
        "code": 200,
        "blocks": serialized
    }


@blocks.put(permission='get')
def update_blocks(request):
    query_language = request.params.get('language')
    blocks_to_be_updated = request.json_body
    serialized = []
    log_blocks = []
    oice = None

    for a in blocks_to_be_updated:
        block_id = a['blockId']
        block = DBSession.query(Block) \
                                    .filter(Block.id == block_id) \
                                    .first()
        if block:
            if not oice:
                oice = block.oice

            # get value before change; for logging
            attrs = {}
            for attr in block.attributes:
                attrs[attr.attribute_definition.attribute_name] = attr.serialized_value

            query_language = check_is_language_valid(query_language) if query_language else block.oice.story.language
            operations.update_block_attributes(DBSession, block, a['attributes'], query_language)
            block_serialize = block.serialize(query_language)
            serialized.append(block_serialize)

            # log data for updating blocks
            log_block = {
                'blockId': block_id,
                'change': [],
                'macroId': block.macro_id,
                'macroName': block.macro.name,
                'macroTagname': block.macro.tagname,
            }
            for attr in block.attributes:
                attr_name = attr.attribute_definition.attribute_name
                old_value = attrs[attr_name] if attr_name in attrs else None
                new_value = attr.value
                if old_value != new_value:
                    log_block['change'].append({
                        'whichFieldChange': attr_name,
                        'beforeChange': old_value,
                        'afterChange': new_value,
                    })
            log_blocks.append(log_block)

    if log_blocks:
        log_dict = {
            'action': 'updateBlock',
            'blocks': log_blocks,
        }
        log_dict = set_basic_info_log(request, log_dict)
        log_block_message(log_dict, request.authenticated_userid, oice)

    return {
        "message": "Update Changed Blocks Succeed",
        "blocks": serialized
    }


# add block and duplicate block(this situation need update attributes)
@block_list.post(permission='set')
def add_block(request):
    # Case 1: only have macro_id -> insert into the first one
    # Case 2: have macro_id and parent_id -> insert into block list(not the first one)
    # Case 3: have macro_id, parent_id, and other keys -> duplicate block
    query_language = request.params.get('language')
    macro_id = request.json_body["macroId"]
    parent_id = request.json_body.get("parentId", None)
    # isDrag is True if add block by drag action; must exist for all cases
    is_drag_action = request.json_body["isDrag"]
    is_duplicate = macro_id and parent_id and len(request.json_body) > 3

    oice = request.context

    macro = DBSession.query(Macro) \
                     .filter(Macro.id == macro_id) \
                     .one()

    block = Block(macro=macro, oice=oice)
    query_language = check_is_language_valid(query_language) if query_language else block.oice.story.language

    parent_block = DBSession.query(Block) \
                            .filter(Block.id == parent_id) \
                            .first() if parent_id else None
    operations.insert_block(DBSession, block, parent_block)
    operations.ensure_block_default_value(DBSession, block, query_language)
    # Add attributes to the block
    if is_duplicate:
        operations.update_block_attributes(DBSession, block, request.json_body, query_language)

    DBSession.flush()

    serialized = block.serialize(query_language)
    serialized['parentId'] = parent_id if parent_id else 0 # For UI knows the inserting position

    log_dict = {
        'action': 'createBlock',
        'blockId': block.id,
        'macroId': macro_id,
        'macroName': macro.name,
        'macroTagname': macro.tagname,
        'parentId': serialized['parentId'],
        'reason': 'drag' if is_drag_action else ('clone' if is_duplicate else 'doubleClick'),
    }
    # Add attributes in log
    attrs = {}
    for attr in block.attributes:
        attrs[attr.attribute_definition.attribute_name] = attr.value
    log_dict.update(attrs)
    log_dict = set_basic_info_log(request, log_dict)
    log_block_message(log_dict, request.authenticated_userid, oice)

    return {
        "message": "ok",
        "block": serialized
    }


@block.put(permission='set')
# move block
def move_block(request):
    parent_id = request.json_body.get("parentId", None)
    block = request.context
    query_language = request.params.get('language')
    query_language = check_is_language_valid(query_language) if query_language else block.oice.story.language
    parent_block = None
    if parent_id:
        parent_block = DBSession.query(Block) \
                                .filter(Block.id == parent_id) \
                                .first()
    operations.move_under(block, parent_block, session=DBSession)
    serialized = block.serialize(query_language)
    serialized['parentId'] = parent_id if parent_id else 0

    log_dict = {
        'action': 'changeOrder',
        'blockId': block.id,
        'macroId': block.macro_id,
        'macroName': block.macro.name,
        'macroTagname': block.macro.tagname,
        'parentId': serialized['parentId'],
    }
    log_dict = set_basic_info_log(request, log_dict)
    log_block_message(log_dict, request.authenticated_userid, block.oice)

    return {
        "message": "ok",
        "block": serialized
    }


@block.post(permission='set')
# save block
def update_block(request):
    block = request.context
    query_language = request.params.get('language')
    query_language = check_is_language_valid(query_language) if query_language else block.oice.story.language
    operations.update_block_attributes(DBSession, block, request.json_body, query_language)
    serialized = block.serialize(query_language)

    return {
        "message": "ok",
        "block": serialized
    }


@block.delete(permission='set')
def delete_block(request):

    block = request.context

    log_dict = {
        'action': 'deleteBlock',
        'blockId': block.id,
        'macroId': block.macro_id,
        'macroName': block.macro.name,
        'macroTagname': block.macro.tagname,
    }
    log_dict = set_basic_info_log(request, log_dict)
    log_block_message(log_dict, request.authenticated_userid, block.oice)

    operations.delete_block(DBSession, block)

    return {"message": "ok"}


@block_translate.post(permission='get')
def post_translate(request):
    block = request.context
    source_language = check_is_language_valid(request.json_body.get("sourceLanguage", None))
    target_language = check_is_language_valid(request.json_body.get("targetLanguage", None))
    if not target_language:
        raise ValidationError("ERR_INVALID_TARGET_LANGUAGE")
    operations.translate_block(block, target_language, source_language)
    return {
        "message": "ok",
        "block": block.serialize(target_language)
    }

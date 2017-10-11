# pylama:ignore=E712
import logging
from cornice import Service
from modmod.exc import ValidationError

from ..models import (
    DBSession,
    StoryFactory,
    LibraryFactory,
    Macro,
    MacroQuery,
    AttributeDefinition
)

log = logging.getLogger(__name__)
macro = Service(name='macro',
                     path='macro',
                     renderer='json')
detail_macro = Service(name='detail_macro',
                       path='macro/{macro_id}',
                       renderer='json')


@macro.get(permission='get')
def list_macro(request):
    macro_list = MacroQuery(DBSession).query()
    return {
        'code': 200,
        'macros': [macro.serialize() for macro in macro_list]
    }


@macro.post(permission='admin_set')
def add_macro(request):
    name = request.json_body.get('chineseName', None)
    tagname = request.json_body.get('name', None)
    content = request.json_body.get('content', None)

    try:
        macro = Macro(
            name=name,
            tagname=tagname,
            content=content,
            macro_type='custom')

    except ValueError as e:
        raise ValidationError(str(e))
    else:
        DBSession.add(macro)
        DBSession.flush()

        return {
            'code': 200,
            'message': 'ok',
            'macro': macro.serialize()
        }


@detail_macro.get(permission='get')
def macro_detail(request):
    request_macro_id = request.matchdict['macro_id']

    macro = DBSession.query(Macro) \
        .filter(Macro.id == request_macro_id) \
        .one()

    attributesDef = DBSession \
        .query(AttributeDefinition) \
        .filter(AttributeDefinition.macro_id == request_macro_id) \
        .all()

    result = macro.serialize()
    result["attributes"] = [attribute_definition.serialize() for attribute_definition in attributesDef]
    return {
        'code': 200,
        'macro': result
    }


@detail_macro.post(permission='admin_set')
def update_macro(request):

    macro_id = request.matchdict['macro_id']
    try:

        macro = DBSession.query(Macro) \
            .filter(Macro.id == macro_id) \
            .one()

        if 'chineseName' in request.json_body:
            macro.name = request.json_body['chineseName']

        if 'name' in request.json_body:
            macro.tagname = request.json_body['name']

        if 'content' in request.json_body:
            macro.content = request.json_body['content']

        if 'isHidden' in request.json_body:
            macro.is_hidden = request.json_body['isHidden']

    except ValueError as e:
        raise ValidationError(str(e))

    else:
        DBSession.add(macro)

        return {
            'code': 200,
            'message': 'ok',
            'macro': macro.serialize()
        }

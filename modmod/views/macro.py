# pylama:ignore=E712
import logging
from cornice import Service
from modmod.exc import ValidationError

from ..models import (
    DBSession,
    Macro,
    MacroFactory,
    MacroQuery,
)

log = logging.getLogger(__name__)

api_macro = Service(
    name='macro',
    path='macro',
    renderer='json',
)

api_macro_id = Service(
    name='detail_macro',
    path='macro/{macro_id}',
    factory=MacroFactory,
    traverse='/{macro_id}',
    renderer='json',
)


@api_macro.get(permission='get')
def list_macro(request):
    macro_list = MacroQuery(DBSession).query()
    return {
        'code': 200,
        'macros': [macro.serialize() for macro in macro_list]
    }


@api_macro.post(permission='admin_set')
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


@api_macro_id.get()
def macro_detail(request):
    macro = request.context

    result = macro.serialize()
    result["attributes"] = [attribute_definition.serialize() for attribute_definition in macro.attribute_definitions]
    return {
        'code': 200,
        'macro': result
    }


@api_macro_id.post(permission='admin_set')
def update_macro(request):
    macro = request.context

    try:
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

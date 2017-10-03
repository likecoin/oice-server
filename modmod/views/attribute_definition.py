from sqlalchemy.exc import IntegrityError
import logging
from cornice import Service
from modmod.exc import ValidationError

from ..models import (
    DBSession,
    AttributeDefinition
)

log = logging.getLogger(__name__)
attribute_definition_add = \
    Service(name='attribute_definition_add',
            path='attribute_definition',
            renderer='json')
attribute_definition_update = \
    Service(name='attribute_definition_update',
            path='attribute_definition/' +
            '{attribute_definition_id}',
            renderer='json')


@attribute_definition_add.post(permission='admin_set')
def add_attribute_definition(request):
    macro_id = request.json_body.get('macroId', None)
    asset_type = request.json_body.get('type', None)
    asset_type_id = request.json_body.get('assetTypeId', None)
    attribute_name = request.json_body.get('name', None)
    name = request.json_body.get('label', None)
    default_value = request.json_body.get('defaultValue', None)
    required = request.json_body.get('required', None)
    localizable = request.json_body.get('localizable', None)
    try:
        attribute_definition = AttributeDefinition(
            macro_id=macro_id,
            asset_type=asset_type,
            asset_type_id=asset_type_id,
            attribute_name=attribute_name,
            name=name,
            required=required,
            default_value=default_value,
            localizable=localizable)
        DBSession.add(attribute_definition)
        DBSession.flush()

    except ValueError as e:
        raise ValidationError(str(e))

    except IntegrityError as e:
        raise ValidationError('Incorrect macro_id or asset_type_id.')
    else:

        return {
            'code': 200,
            'message': 'ok',
            'attributeDefinition': attribute_definition.serialize()
        }


@attribute_definition_update.post(permission='admin_set')
def update_attribute_definition(request):

    object_id = request.matchdict['attribute_definition_id']
    try:

        attribute_definition = DBSession.query(AttributeDefinition) \
                                        .filter(
                                            AttributeDefinition.id == object_id
                                         ) \
                                        .one()

        for key in ['type', 'assetTypeId', 'name',
                    'label', 'required', 'defaultValue', 'localizable']:
            if key in request.json_body:
                setattr(attribute_definition, key, request.json_body[key])

        DBSession.add(attribute_definition)
        DBSession.flush()

    except ValueError as e:
        raise ValidationError(str(e))
    else:
        return {
            'code': 200,
            'message': 'ok',
            'attributeDefinition': attribute_definition.serialize()
        }

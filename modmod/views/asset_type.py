from cornice import Service
import logging

from ..models import (
    DBSession,
    AssetType
)

log = logging.getLogger(__name__)
asset_type = Service(name='asset_type',
                          path='asset_type',
                          renderer='json')


@asset_type.get(permission='get')
def list_asset_type(request):

        asset_types = DBSession.query(AssetType).all()

        return {
        	'code': 200,
        	'assetTypes': [type_.serialize() for type_ in asset_types]
        }

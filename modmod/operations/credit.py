from sqlalchemy.sql.expression import true, false

from ..models import (
    DBSession,
    Attribute,
    AssetQuery,
    AssetType,
    Block,
    Oice,
    StoryQuery,
    UserQuery,
)
import transaction
import logging

log = logging.getLogger(__name__)

def get_oice_credit(oice):
    # Get list of asset_ids used
    asset_ids = []

    block_ids = DBSession.query(Block.id) \
                 .filter(Block.oice_id == oice.id) \
                 .all()
    block_ids = [b.id for b in block_ids]
    asset_ids = DBSession.query(Attribute.asset_id) \
                 .filter(Attribute.asset_id.isnot(None)) \
                 .filter(Attribute.block_id.in_(block_ids)) \
                 .distinct()
    asset_ids = [a.asset_id for a in asset_ids]

    # Get all asset types
    asset_types = DBSession.query(AssetType.folder_name).all()

    grouped_credits = {}
    for asset_type in asset_types:
        grouped_credits[asset_type.folder_name] = []

    # Get list of assets used
    assets = AssetQuery(DBSession). \
        get_by_ids(asset_ids)

    # Assign credit users by asset types
    for asset in assets:
        for type_ in asset.asset_types:
            grouped_credits[type_.folder_name].extend(asset.users)

    all_users = set()
    for asset_type in grouped_credits.keys():
        grouped_users = set(grouped_credits[asset_type])
        all_users |= grouped_users
        # Remove duplicate user
        # and serialize
        grouped_credits[asset_type] = [u.serialize() for u in grouped_users]
        grouped_credits[asset_type].sort(key=lambda user: user["displayName"])

    # Add director group
    directors = oice.story.users[:1] # For now, just show the author
    directors.sort(key=lambda user: user.display_name)
    grouped_credits['director'] = [u.serialize_credit() for u in directors]

    mini_credits = grouped_credits['director'] + [u.serialize_credit() for u in all_users - set(directors)] # Directors first

    return {
        'grouped': grouped_credits,
        'mini': mini_credits
    }

def get_story_credit(story_id):
    story = StoryQuery(DBSession).get_story_by_id(story_id=story_id)
    oice_ids = [o.id for o in story.oice]

    # Get list of asset_ids used
    asset_ids = []

    block_ids = DBSession.query(Block.id) \
                 .filter(Block.oice_id.in_(oice_ids)) \
                 .all()
    block_ids = [b.id for b in block_ids]
    asset_ids = DBSession.query(Attribute.asset_id) \
                 .filter(Attribute.asset_id.isnot(None)) \
                 .filter(Attribute.block_id.in_(block_ids)) \
                 .distinct()
    asset_ids = [a.asset_id for a in asset_ids]

    # Remove duplicate asset_id
    asset_ids = set(asset_ids)

    # Get all asset types
    asset_types = DBSession.query(AssetType.folder_name).all()

    credits = {}
    for asset_type in asset_types:
        credits[asset_type.folder_name] = []

    # Get list of assets used
    assets = AssetQuery(DBSession). \
        get_by_ids(asset_ids)

    # Assign credit users by asset types
    for asset in assets:
        for type_ in asset.asset_types:
            credits[type_.folder_name].extend([u for u in asset.users])

    for asset_type in credits.keys():
        # Remove duplicate user
        # and serialize
        credits[asset_type] = [user.serialize() for user in set(credits[asset_type])]
        credits[asset_type].sort(key=lambda user: user["displayName"])
    return credits

def get_user_story_credit(user_id):
    user = UserQuery(DBSession).get_user_by_id(id=user_id)
    asset_ids = set()
    libraries = set()

    for asset in user.assets:
        if not asset.is_deleted:
            asset_ids.add(asset.id)
            if asset.library.is_public and not asset.library.is_deleted:
                libraries.add(asset.library)

    block_ids = DBSession.query(Attribute.block_id) \
                 .filter(Attribute.asset_id.in_(asset_ids)) \
                 .distinct()
    block_ids = [b.block_id for b in block_ids]

    oice_ids = DBSession.query(Block.oice_id) \
                .filter(Block.id.in_(block_ids)) \
                .distinct()
    oice_ids = [o.oice_id for o in oice_ids]

    story_ids = DBSession.query(Oice.story_id) \
                .filter(Oice.id.in_(oice_ids)) \
                .filter(Oice.is_deleted == false()) \
                .distinct()
    story_ids = [s.story_id for s in story_ids]

    stories = StoryQuery(DBSession).get_story_by_id_list(story_ids)

    credits = {}
    credits["libraries"] = [library.serialize() for library in libraries]
    credits["stories"] =[story.serialize() for story in stories]

    return credits

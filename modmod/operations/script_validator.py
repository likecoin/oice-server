import logging
from ..models import (
    DBSession,
    Oice
)

from sqlalchemy.orm import joinedload
log = logging.getLogger(__name__)


class ScriptValidator(object):

    def __init__(self, story=None, oice=None):
        self.story = story
        self.oice = oice
        self._ks_map = None

    @property
    def ks_map(self):
        if self._ks_map is None:
            self._ks_map = {}
            if self.oice is not None:
                self._ks_map['first.ks'] = self.oice
            else:
                oice_query = DBSession.query(Oice) \
                                    .options(joinedload('blocks')) \
                                    .filter(Oice.story_id == self.story.id)
                for oice in oice_query:
                    self._ks_map[oice.filename] = oice
        return self._ks_map

    def get_story_errors(self):
        story_errors = []
        if "first.ks" not in self.ks_map.keys():
            story_errors.append(
                "first.ks not found in story, it is required"
            )
        return story_errors

    def get_errors(self):
        errors = {}
        log.debug(self.ks_map)
        for (filename, ks) in self.ks_map.items():
            this_errors = self.errors_in_KS(ks)
            if this_errors:
                errors[filename] = this_errors
        return errors

    def errors_in_KS(self, ks):
        errors = []
        for block in ks.blocks:
            this_errors = self.errors_in_block(block)
            if this_errors:
                errors.append({
                    'block': block.serialize(),
                    'errors': this_errors
                })

        return errors

    def errors_in_block(self, block):
        errors = {}

        attrs = {}
        for attr in block.attributes:
            attrs[attr.attribute_definition.attribute_name] = attr

        for attr_def in block.macro.attribute_definitions:
            is_asset = attr_def.is_asset
            name = attr_def.attribute_name
            if attr_def.required:
                if name not in attrs:
                    errors[name] = name+' is required'
                else:
                    value = attrs[name].value
                    asset_id = attrs[name].asset_id
                    if is_asset and (not asset_id) \
                        or (not is_asset) and (not value):
                        errors[name] = name+' is required'
        return errors

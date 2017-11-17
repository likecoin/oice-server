import json
import logging
from sqlalchemy.orm import joinedload
from ..models import (
    DBSession,
    Oice
)


log = logging.getLogger(__name__)


class ScriptValidator(object):

    def __init__(self, story=None, oice=None):
        self.story = story
        self.oice = oice
        self._oice_map = None
        self._labels = None
        self._jump_targets = None
        self._jump_target_map = None

    @property
    def oice_map(self):
        if self._oice_map is None:
            self._oice_map = {}
            if self.oice is not None:
                self._oice_map['first.ks'] = self.oice
            else:
                oices = DBSession.query(Oice) \
                                 .options(joinedload('blocks')) \
                                 .filter(Oice.story_id == self.story.id)
                for oice in oices:
                    self._oice_map[oice.filename] = oice
        return self._oice_map

    @property
    def labels(self):
        if self._labels is None:
            self._labels = set()
        return self._labels

    @property
    def jump_target_map(self):
        if self._jump_target_map is None:
            self._jump_target_map = {}
        return self._jump_target_map

    @property
    def jump_targets(self):
        if self._jump_targets is None:
            self._jump_targets = set()
        return self._jump_targets

    @staticmethod
    def get_asset_required_error_code(attribute_definition):
        return 'ERR_OICE_VALIDATE_ASSET_REQUIRED_' + attribute_definition.asset_type_key.upper()

    def define_label(self, label):
        self.labels.add(label)

    def define_jump_target(self, block, attribute_name, target):
        self.jump_targets.add(target)

        if target not in self.jump_target_map:
            self.jump_target_map[target] = []
        self.jump_target_map[target].append((block, attribute_name, target))

    def get_story_errors(self):
        story_errors = []
        if "first.ks" not in self.oice_map.keys():
            story_errors.append(
                "first.ks not found in story, it is required"
            )
        return story_errors

    def get_errors(self):
        errors = {}

        for (filename, ks) in self.oice_map.items():
            this_errors = self.errors_in_oice(ks)
            if this_errors:
                errors[filename] = this_errors
        return errors

    def errors_in_oice(self, oice):
        error_blocks_map = {}
        error_map = {}

        for block in oice.blocks:
            block_errors = self.errors_in_block(block)
            if block_errors:
                error_blocks_map[block.id] = block
                error_map[block.id] = block_errors

        # Validate jump targets
        undefined_targets = self.jump_targets - self.labels
        if undefined_targets:

            for target in undefined_targets:
                for block, attribute_name, value in self.jump_target_map[target]:
                    if block.id not in error_blocks_map:
                        error_blocks_map[block.id] = block

                    if block.id not in error_map:
                        error_map[block.id] = []

                    error_map[block.id].append({
                        'attributeName': attribute_name,
                        'code': 'ERR_OICE_VALIDATE_INVALID_JUMP_TARGET',
                        'value': target,
                    })

        return [
            {
                "block": block.serialize_min(),
                'errors': error_map[block.id],
            }
            for block in sorted(error_blocks_map.values(), key=lambda b: b.position)
        ]

    def errors_in_block(self, block):
        errors = []

        macro_name = block.macro.tagname
        existing_attributes = {attr.attribute_definition.attribute_name: attr for attr in block.attributes}

        for attribute_definition in block.macro.attribute_definitions:

            attribute_name = attribute_definition.attribute_name
            is_asset       = attribute_definition.is_asset

            if attribute_definition.required:

                if attribute_name not in existing_attributes:

                    if is_asset:
                        code = ScriptValidator.get_asset_required_error_code(attribute_definition)

                    elif macro_name == 'characterdialog' and attribute_name == 'character':
                        code = 'ERR_OICE_VALIDATE_CHARACTER_REQUIRED'

                    else:
                        code = 'ERR_OICE_VALIDATE_ATTRIBUTE_REQUIRED'

                    errors.append({
                        'attributeName': attribute_name,
                        'code': code,
                    })

                else:
                    attribute = existing_attributes[attribute_name]
                    value     = attribute.value
                    asset_id  = attribute.asset_id

                    if is_asset and not asset_id \
                       or not is_asset and not value:
                        errors.append({
                            'attributeName': attribute_name,
                            'code': ScriptValidator.get_asset_required_error_code(attribute_definition)
                        })

                    elif macro_name == 'label'  and attribute_name == 'name':
                        self.define_label(value)

                    elif macro_name == 'jump'   and attribute_name == 'target':
                        self.define_jump_target(block, attribute_name, value)

                    elif macro_name == 'option' and attribute_name == 'answers':
                        try:
                            answers = json.loads(value)

                        except ValueError:
                            errors.append({
                                'attributeName': attribute_name,
                                'code': 'ERR_OICE_VALIDATE_INVALID_ANSWERS_OBJECT'
                            })

                        else:
                            for answer in answers:
                                target = answer['target']

                                if target:
                                    self.define_jump_target(block, attribute_name, target)

                                else:
                                    errors.append({
                                        'attributeName': attribute_name,
                                        'code': 'ERR_OICE_VALIDATE_INVALID_OPTION_TARGET',
                                        'value': target,
                                    })

        return errors

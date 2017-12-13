# FIXME
# pylama:ignore=C901

import json
import logging
import re

from urllib.parse import quote
from modmod.exc import ValidationError
from subprocess import check_output, CalledProcessError
from . import character_script_data
from . import script_export_default


log = logging.getLogger(__name__)


class ScriptVisitor(object):

    def __init__(self, story=None, characters=[], scale_factor=1):
        self.story = story
        self._character_id_map = {
            character.id: character
            for character in characters
        }
        self.scale_factor = scale_factor
        self._initialize_oice()

    def _initialize_oice(self):
        # Need to reset before visiting oice
        # Character sence map
        self._cs_map = {
            'left': None,
            'middle': None,
            'right': None
        }
        self.autoplay = False
        self.prev_character = None
        self.prev_character_name = None
        self.prev_message_block = None

    def _post_oice_action(self, action):
        if not action or type(action) is not dict:
            return ''

        if 'payload' in action:
            action['payload'] = json.dumps(action['payload'])

        return '[o2_iscript]new Tag("postoiceaction", %s).run()[o2_endscript]\n' % str(action)

    def visit_default_block(self, block, language):
        script = "@" + block.macro.tagname

        if block.macro.tagname == 'clearmessage':
            self.prev_character_name = None

        for attr in block.attributes:
            if attr.attribute_definition.attribute_name in script_export_default.SCALABLE_ATTRIBUTES:
                if attr.value:
                    attr.value = int(float(attr.value) * self.scale_factor)

            if block.macro.tagname in script_export_default.FADING_AUDIO_MACROS \
                    and attr.attribute_definition.attribute_name == 'time' \
                    and int(attr.value) < 1:
                # Fading time cannot less than 1
                attr.value = 1

            if attr.attribute_definition.asset_type == 'reference':
                if attr.attribute_definition.attribute_name == 'rule' or not attr.asset_id:
                    continue

            elif not attr.value:
                continue

            script += ' ' + attr.accept(self, language)

        return script + '\n'

    def visit_autoplay_block(self, block, language):
        script = self.visit_default_block(block, language)
        self.autoplay = True
        return script

    def visit_Cancelautomode_block(self, block, language):
        script = self.visit_default_block(block, language) if self.autoplay else ''
        self.autoplay = False
        return script

    def visit_item_block(self, block, language):
        script = "@" + block.macro.tagname
        for attr in block.attributes:
            if attr.attribute_definition.attribute_name == 'storage' and attr.asset_id:
                # Get item size and calculate the position on screen
                image_path = attr.asset.storage.url

                try:
                    command = [
                        "identify",
                        "-format",
                        '[%w,%h]',
                        str(image_path)
                    ]
                    output_size = check_output(command).decode("utf-8")
                except CalledProcessError as e:
                    raise 'Error occurs when getting item image size: %s' % str(e)

                width, height = json.loads(output_size)
                screen_size = script_export_default.SCREEN_SIZE
                top = int(self.scale_factor * (screen_size - height) / 2)
                left = int(self.scale_factor * (screen_size - width) / 2)
                position = " top=%d left=%d" % (top, left)
                script += position
            elif not attr.value:
                continue

            script += " " + attr.accept(self, language)

        return script

    def visit_jump_block(self, block, language):
        attrs = block.get_localized_attributes()
        return '@oice_jump storage="%(storage)s" target="%(target)s"\n' % {
            'storage': language + '.ks',
            'target': attrs['target'],
        }

    def visit_label_block(self, block, language):
        attrs = block.get_localized_attributes(language)

        # TODO: Temporal fix on missing character name after jump
        # Reset scene
        self.prev_character = None
        self.prev_character_name = None
        self.prev_message_block = None

        value = "*"
        if 'name' in attrs:
            value += attrs['name']
        else:
            raise ValidationError('ERR_LABEL_NAME_NOT_FOUND +' + str(attrs) + ' ' + language)
        if 'caption' in attrs:
            value += "|" + attrs['caption']

        return value + "\n@optionclear"

    def visit_comment_block(self, block, language):
        attrs = block.get_localized_attributes(language)

        return ';' + attrs.get('text', '') + '\n'

    def visit_option_block(self, block, language):
        attrs = block.get_localized_attributes(language)
        question = attrs.get('question', '')
        script = '@optionstart\n' + ScriptVisitor.print_dialog_text(question) + '\n'

        if 'answers' in attrs:
            try:
                answers = json.loads(attrs['answers'])
            except ValueError:
                raise ValidationError(str(block.id) + 'ERR_OPTION_BLOCK_ANSWERS_NOT_IN_JSON_FORMAT')
            else:
                for answer_index, answer in enumerate(answers):
                    script += '@optionanswer storage="%s" target="%s" text="%s" oiceid=%d blockid=%d index=%d\n' % (
                        language + '.ks',
                        answer['target'],
                        quote(answer['content']).replace('%', '!'),  # Encode text
                        block.oice_id,
                        block.id,
                        answer_index,
                    )
        else:
            raise ValidationError('ERR_OPTION_BLOCK_ANSWERS_NOT_FOUND')

        script += self._post_oice_action({
            'type': 'oice.didShowOptions',
            'payload': {
                'oiceId': block.oice_id,
                'blockId': block.id,
                'question': question,
                'answers': answers,
            },
        })

        script += '@optionend\n'

        return script

    def visit_fgExitRight_block(self, block, language):
        self._cs_map['right'] = None
        return character_script_data.fg_exit['right'] + "\n"

    def visit_fgExitLeft_block(self, block, language):
        self._cs_map['left'] = None
        return character_script_data.fg_exit['left'] + "\n"

    def visit_fgExitMiddle_block(self, block, language):
        self._cs_map['middle'] = None
        return character_script_data.fg_exit['middle'] + "\n"

    def _get_waitclick(self):
        return ('@autowait' if self.autoplay else '@l') + "\n"

    def visit_addTalk_block(self, block, language):
        attrs = block.get_localized_attributes(language)
        script = ''

        # dialogs
        if 'talk' in attrs:
            script += self._print_dialog(attrs['talk'])

        script += self._get_waitclick()
        script += self._get_waitse(attrs)

        self.prev_message_block = block

        return script

    def visit_aside_block(self, block, language):
        attrs = block.get_localized_attributes(language)

        name = attrs.get('name', None)
        if self.prev_character_name != name:
            self.prev_character_name = name

        full_screen = bool(attrs.get('fullscreen'))

        script = ''

        # Display name
        if not full_screen and name:
            script += '@charactername name="%s"\n' % name
        else:
            script += '@asideTalk\n'

        # Display dialogs
        if 'text' in attrs:
            script += self._print_dialog(attrs['text'], full_screen=full_screen, fade_in=full_screen or not name)

        script += self._get_waitclick()
        script += self._get_waitse(attrs)

        self.prev_character = None
        self.prev_message_block = block

        return script

    def visit_characterdialog_block(self, block, language):
        attrs = block.get_localized_attributes(language)
        script = ''

        character = self._character_id_map.get(int(attrs['character']), None)
        if character is None:
            return script

        consecutive = self.prev_character and self.prev_character.id == character.id

        if not consecutive:
            script += '@cm\n'

        # Render character image
        fg = attrs.get('fg', None)
        position = attrs.get('position', 'left')
        fliplr = attrs.get('fliplr', None)
        character_scene = CharacterScene(character, fg, fliplr)

        is_dim = attrs.get('dim', False)
        is_move = attrs.get('move', False)

        script += self._display_character(position, character_scene, is_dim, is_move)

        is_hidden_dialog = attrs.get('hidedialog', False)

        # Render character name if not the talking character
        if not is_hidden_dialog:
            # TODO:
            # Since client is not ready for character localization,
            # therefore we hardcode zh-HK for character name
            character_name = character.get_name('zh-HK')
            if character.is_generic:
                customized_name = attrs.get('name', None)
                if customized_name:
                    character_name = customized_name

            if character_name and (self.prev_character_name != character_name or not consecutive):
                self.prev_character_name = character_name
                script += '@charactername name="%s"\n' % character_name

        # Render dialogs
        if 'dialog' in attrs and not is_hidden_dialog:
            script += self._print_dialog(attrs['dialog'])

        if not is_hidden_dialog:
            script += self._get_waitclick()
        else:
            script += '@wait time=300\n'

        script += self._get_waitse(attrs)

        if attrs.get('fgexit', False):
            script += self._fg_exit(position, character_scene)

        self.prev_character = character
        self.prev_message_block = block

        return script

    def _get_waitse(self, attrs):
        script = ""
        if attrs.get('waitse', False):
            for track in range(0, 3):
                script += '@ws buf=' + str(track) + ' canskip="true"\n'
        return script

    @staticmethod
    def print_dialog_text(dialog_text):
        dialogs = dialog_text.strip().splitlines()

        script = ''
        for line, dialog in enumerate(dialogs):
            if dialog:
                if line > 0:
                    script += "[r]\n"

                # Handle special symobl of KAG
                dialog = re.sub(r'([\t;@#&*%]+)',
                                r'[o2_iscript]tf._specialChars = "\1";[o2_endscript][ch text=&tf._specialChars]',
                                dialog)

                script += dialog

        return script + "\n"

    def _print_dialog(self, dialog_text, full_screen=False, fade_in=False):
        script = "@dialog fullscreen=%(fullscreen)s fadein=%(fadein)s\n" % {
            'fullscreen': 'true' if full_screen else 'false',
            'fadein': 'true' if fade_in else 'false',
        }
        script += ScriptVisitor.print_dialog_text(dialog_text)
        return script + "\n"

    def _display_character(self, position, character_scene, is_dim=True, is_move=True):
        character = character_scene.character
        script = ""
        to_bright = False
        is_dim = str(is_dim).lower()
        is_move = str(is_move).lower()
        two_sides = ['left', 'right']
        if position in two_sides:
            if self._cs_map['middle']:
                script += self._fg_exit(
                    'middle',
                    self._cs_map['middle'])

            for scene_pos in two_sides:
                if self._cs_map[scene_pos] is None:
                    continue

                if scene_pos == position:
                    if self._cs_map[scene_pos].character_id ==\
                            character.id and self._cs_map[scene_pos].dark:
                        to_bright = True
                else:
                    if not self._cs_map[scene_pos].dark:
                        script += self._fg_dark(
                            scene_pos,
                            self._cs_map[scene_pos])

        elif position == 'middle':
            for scene_pos in ['left', 'right']:
                if self._cs_map[scene_pos]:
                    script += self._fg_exit(
                        scene_pos,
                        self._cs_map[scene_pos])

        if to_bright:
            script += self._fg_bright(position, character_scene, is_dim, is_move)
        else:
            script += self._fg_show(position, character_scene, is_dim, is_move)

        self._cs_map[position] = character_scene

        return script

    def _fg_show(self, position, character_scene, is_dim='true', is_move='true'):
        character_scene.dark = False

        character = character_scene.character
        fg = character_scene.fg
        fliplr = character_scene.fliplr

        script = character_script_data.fg_show[position] % {
            'key': character.uuid,
            'fg': fg.accept(self) if fg else '',
            'dim': is_dim,
            'move': is_move,
        }

        if fliplr is not None:
            script += ' fliplr="%d"' % (1 if fliplr else 0)

        return script + "\n"

    def _fg_dark(self, position, character_scene):
        character_scene.dark = True

        character = character_scene.character
        fg = character_scene.fg
        fliplr = character_scene.fliplr

        script = character_script_data.fg_to_dark[position] % {
            'key': character.uuid,
            'fg': fg.accept(self) if fg else ''
        }

        if fliplr is not None:
            script += ' fliplr="%d"' % (1 if fliplr else 0)

        return script + "\n"

    def _fg_bright(self, position, character_scene, is_dim='true', is_move='true'):
        character_scene.dark = False

        character = character_scene.character
        fg = character_scene.fg
        fliplr = character_scene.fliplr

        script = character_script_data.fg_to_bright[position] % {
            'key': character.uuid,
            'fg': fg.accept(self) if fg else '',
            'dim': is_dim,
            'move': is_move,
        }

        if fliplr is not None:
            script += ' fliplr="%d"' % (1 if fliplr else 0)

        return script + "\n"

    def _fg_exit(self, position, character_scene):
        self._cs_map[position] = None
        self.prev_character = None
        return character_script_data.fg_exit[position] + "\n"

    def visit_attribute(self, attribute, language):
        name = attribute.attribute_definition.attribute_name
        if attribute.attribute_definition.asset_type == "reference":
            value = attribute.asset.accept(self)
        elif attribute.attribute_definition.asset_type == "color":
            value = re.sub('^#', '0x', attribute.value)
        elif attribute.attribute_definition.localizable:
            value = attribute.block.get_localizable_attributes(language)[name]
        else:
            value = attribute.value
        return name + '="' + value + '"'

    def visit_asset(self, asset):
        return asset.export_filename

    def visit_oice(self, oice, language):
        self._initialize_oice()
        script = ''

        for block in oice.blocks:
            script += ";#%(id)s\n%(block)s\n" % ({
                "id": block.id,
                "block": block.accept(self, language)
            })

        return script

    def visit_story(self, story):
        scripts = {}
        for oice in story.oice:
            scripts[oice.filename] = oice.accept(self)
        return scripts


class CharacterScene(object):
    """Store the character parameter when character enter the scene"""
    def __init__(self, character, fg, fliplr=False, dark=False):
        self.character = character
        self.fg = fg
        self.fliplr = fliplr
        self.dark = dark

    @property
    def character_id(self):
        return self.character.id


class CharacterVisitor(object):

    def visit_default_block(self, block):
        return set(
            [attribute.value for attribute
             in block.attributes
             if attribute.attribute_definition.attribute_name == 'character']
        )

    def visit_oice(self, oice):
        used_characters = set()
        for block in oice.blocks:
            character_set = block.accept(self)
            used_characters.update(character_set)
        return used_characters


class AssetVisitor(object):

    def visit_default_block(self, block):
        return set(
            [attr.asset for attr
             in block.attributes
             if attr.asset is not None]
        )

    def visit_asset(self, asset):
        return asset.export_filename_with_ext

    def visit_oice(self, oice):
        used_assets = set()
        for block in oice.blocks:
            asset_set = block.accept(self)
            used_assets.update(asset_set)
        return used_assets

    def visit_story(self, story):
        used_assets = set()
        for oice in story.oice:
            used_assets.update(oice.accept(self))
        return used_assets


class MacroVisitor(object):

    def visit_default_block(self, block):
        return set([block.macro])

    def visit_oice(self, oice):
        used_macro = set()
        for block in oice.blocks:
            macro_set = block.accept(self)
            used_macro.update(macro_set)
        return used_macro

    def visit_story(self, story):
        used_macro = set()
        for oice in story.oice:
            used_macro.update(oice.accept(self))
        return used_macro

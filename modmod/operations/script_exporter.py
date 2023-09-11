import fileinput
import json
import logging
import os
import shutil
import subprocess
import tempfile
import zipfile

from . import script_export_default as EXPORT_DEFAULT
from .script_export_serializer import (
    ScriptVisitor,
    AssetVisitor,
    MacroVisitor,
    CharacterVisitor,
)
from ..models import (
    DBSession,
    CharacterQuery,
)


log = logging.getLogger(__name__)


PROJECT_FOLDERS = [
    'bgimage',
    'bgm',
    'fgimage',
    'font',
    'image',
    'others',
    'rule',
    'sound',
    'video',
    'scenario',
]


RESIZE_FOLDERS = [
    'bgimage',
    'fgimage',
    'image',
]


# Utils
def create_if_not_exist(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)


def subpath(base_path, folder_name):
    for name in os.listdir(base_path):
        if name.lower() == folder_name.lower():
            return os.path.join(base_path, name)
    return None


# Generate path for [move] tag
def get_move_path_string(x, y):
    return '({}, {}, 255)'.format(x, y)


class ScriptExporter(object):
    def __init__(self, resize_script, oice, export_path,
                 oice_view_url=None, oice_communication_url=None,
                 og_image_button_url=None, og_image_origin_url=None,
                 characters=[],
                 scale_factor=0.5):
        self.resize_script = resize_script
        self.export_path = export_path
        self.oice = oice
        self.title = oice.story.name + ' - ' + oice.filename
        self.oice_view_url = oice_view_url
        self.oice_communication_url = oice_communication_url if oice_communication_url else ''
        self.is_offline = oice_communication_url is None
        self.og_image_button_url = og_image_button_url
        self.og_image_origin_url = og_image_origin_url
        self.script_visitor = ScriptVisitor(oice.story, characters, scale_factor)
        self.scale_factor = scale_factor

        self._used_assets = None
        self._used_macro = None
        self._used_character_ids = None

    @property
    def used_macro(self):
        if self._used_macro is None:
            self._used_macro = self.oice.accept(MacroVisitor())
        return self._used_macro

    @property
    def used_assets(self):
        if self._used_assets is None:
            self._used_assets = self.oice.accept(AssetVisitor())
        return self._used_assets

    @property
    def used_character_ids(self):
        if self._used_character_ids is None:
            self._used_character_ids = self.oice.accept(CharacterVisitor())
        return self._used_character_ids

    # Calculate character config
    def get_character_config(self, character):
        # Initialize
        screen_height = screen_width = int(float(EXPORT_DEFAULT.SCREEN_SIZE) * self.scale_factor)
        y_offset = x_offset = int(float(EXPORT_DEFAULT.CHARACTER_CONFIG["offset"]) * self.scale_factor)
        character_width = int(float(character.width) * self.scale_factor)
        character_height = int(float(character.height) * self.scale_factor)

        config = {
            'edgecolor': EXPORT_DEFAULT.CHARACTER_CONFIG["edgecolor"],
            'frame': EXPORT_DEFAULT.CHARACTER_CONFIG["nameframe"],
            'name': character.get_name(),
        }

        # Apply overriding config first
        try:
            character_override_config = json.loads(character.config)
        except ValueError as e:
            config['_error'] = str(e)
        else:
            for key in EXPORT_DEFAULT.OVERRIDABLE_CHARACTER_CONFIG_ITEMS:
                if key in character_override_config:
                    if key == 'edgecolor':
                        config[key] = character_override_config[key]
                    else:
                        try:
                            config[key] = int(float(character_override_config[key]) * self.scale_factor)
                        except:
                            log.error("Error scaling key: " + key)
                            log.error("Value: " + character_override_config[key])

        # Calculate missing config only

        # X-axis
        if 'xl' not in config:
            if character_width < screen_width:
                config['xl'] = int((screen_width / 2 - character_width) / 2)
            else:
                config['xl'] = 0

        if 'xr' not in config:
            config['xr'] = screen_width - config['xl'] - character_width

        if 'xm' not in config:
            config['xm'] = int((screen_width - character_width) / 2)

        # Y-axis
        if 'yl' not in config:
            if character_height < screen_height:
                config['yl'] = screen_height - character_height
            else:
                config['yl'] = 0

        if 'yr' not in config:
            config['yr'] = config['yl']

        if 'ym' not in config:
            config['ym'] = config['yl']

        # Dimmed coordinates
        if 'xDl' not in config:
            config['xDl'] = config['xl'] - x_offset
        if 'xDm' not in config:
            config['xDm'] = config['xm']
        if 'xDr' not in config:
            config['xDr'] = config['xr'] + x_offset

        if 'yDl' not in config:
            config['yDl'] = config['yl'] + y_offset
        if 'yDm' not in config:
            config['yDm'] = config['ym'] + y_offset
        if 'yDr' not in config:
            config['yDr'] = config['yr'] + y_offset

        config['pathl'] = get_move_path_string(config['xl'], config['yl'])
        config['pathm'] = get_move_path_string(config['xm'], config['ym'])
        config['pathr'] = get_move_path_string(config['xr'], config['yr'])
        config['pathDl'] = get_move_path_string(config['xDl'], config['yDl'])
        config['pathDm'] = get_move_path_string(config['xDm'], config['yDm'])
        config['pathDr'] = get_move_path_string(config['xDr'], config['yDr'])

        return config

    def export_used_character_config(self):
        character_configs = {}

        used_characters = CharacterQuery(DBSession).fetch_by_ids(self.used_character_ids)
        for character in used_characters:
            character_configs[character.uuid] = self.get_character_config(character)

        serialized_character_configs = json.dumps(character_configs, sort_keys=True, indent=2)

        return '[o2_iscript]\nch = ' + \
               serialized_character_configs + \
               '\n[o2_endscript]\n' + \
               EXPORT_DEFAULT.KS_SCRIPT_RETURN

    def export_asset(self, asset, filename, data_path):
        folder = subpath(data_path, asset.asset_types[0].folder_name)
        if folder is None:
            folder = os.path.join(data_path, asset.asset_types[0].folder_name)
        create_if_not_exist(folder)

        target_path = os.path.join(folder, filename)
        shutil.copyfile(asset.storage.dst, target_path)

        # If the asset file is kind of zip file
        if asset.content_type == 'application/zip':
            # Unzip to tmp/
            temp_extract_path = os.path.join(folder, 'tmp')
            zip_ref = zipfile.ZipFile(target_path, 'r')
            zip_ref.extractall(temp_extract_path)
            zip_ref.close()
            # Remove the zip
            os.remove(target_path)
            # Rename and move the extracted file to original folder
            for root, dirs, files in os.walk(temp_extract_path):
                for asset_filename in files:
                    new_asset_filename = os.path.splitext(filename)[0]  # filename
                    asset_filename_extension = os.path.splitext(asset_filename)[1]  # extension
                    shutil.move(
                        os.path.join(root, asset_filename),
                        os.path.join(folder,new_asset_filename + asset_filename_extension)
                    )
                # Remove the tmp/ foler
                shutil.rmtree(temp_extract_path)

    def export_assets(self, data_path):
        # Add assets
        asset_map = {}

        for asset in self.used_assets:
            filename = asset.accept(AssetVisitor())
            asset_map[filename] = asset

        for (filename, asset) in asset_map.items():
            self.export_asset(asset, filename, data_path)

        # Resize all image assets
        for folder in RESIZE_FOLDERS:
            subprocess.call([self.resize_script, os.path.join(data_path, folder), "%d%%" % (self.scale_factor * 100)])

    def create_novelspherejs_project_from_oice(self):
        # Initial project from template
        project_dir = tempfile.mkdtemp()
        data_dir = os.path.join(project_dir, 'data')
        scenario_dir = os.path.join(data_dir, 'scenario')
        plugin_dir = os.path.join(project_dir, 'plugin')

        file_parent_dir = os.path.dirname(os.path.abspath(__file__))
        template_dir = os.path.abspath(os.path.join(file_parent_dir, '..', 'res', 'novelspherejs', 'template_project'))

        shutil.copytree(os.path.join(template_dir, 'data'), data_dir)
        shutil.copytree(os.path.join(template_dir, 'plugin'), plugin_dir)

        for folder_name in PROJECT_FOLDERS:
            create_if_not_exist(os.path.join(data_dir, folder_name))

        # Generate config.json
        config = EXPORT_DEFAULT.NOVELSPHERE_CONFIG
        config['title'] = self.title
        config['defaultLanguage'] = self.oice.story.language

        # Adjust config based on scale factor
        for attr in EXPORT_DEFAULT.SCALABLE_CONFIG_ITEMS:
            if attr in config:
                config[attr] = int(float(config[attr]) * self.scale_factor)

        config_script = json.dumps(config, ensure_ascii=False, indent=4)

        with open(os.path.join(project_dir, 'config.json'), 'w') as config_file:
            config_file.write(config_script)

        # Generate .ks script files in different languages
        ks_files = dict()

        script = EXPORT_DEFAULT.FIRST_KS_HEADER + EXPORT_DEFAULT.PRE_OICE_SCRIPT

        languages = self.oice.story.supported_languages
        for index, language in enumerate(languages):
            if len(languages) > 1:
                if index == 0:
                    script += '[if '
                elif index != len(languages) - 1:
                    script += '[elsif '
                else:
                    script += '[else]'

                if index != len(languages) - 1:
                    script += '''o2_exp="/^%s/i.test(ev.query.lang)"]''' % language

                script += '\n'

            script += '''@call storage="%s.ks"\n@jump target="endOice"\n''' % language

            ks_files[language] = self.oice.accept(self.script_visitor, language) + '\n@return'

        if len(languages) > 1:
            script += '[endif]\n'

        script += EXPORT_DEFAULT.POST_OICE_SCRIPT

        ks_files['first'] = script

        for filename, script in ks_files.items():
            with open(os.path.join(scenario_dir, filename + '.ks'), 'w') as file:
                file.write(script)

        # Include default variables
        # Since config.json cannot be retrieved in ks so we inject some values of it into ks variables
        # which can be retrieved by `&tf.oiceDefaults` in ks and `tf.oiceDefaults` in JS
        oice_defaults = {
            # General
            'viewSize': config['scHeight'],
            'scaleFactor': self.scale_factor,
            'communicationURL': self.oice_communication_url,
            # Text
            'fontColor': config['messageLayerDefaultFontColor'],
            'fontSize': config['messageLayerDefaultFontSize'],
            'fontFace': config['messageLayerDefaultFontFace'],
            'lineSpacing': config['messageLayerDefaultStyleLineSpacing'],
            # Message Layer
            'messageLayer': {
                'minPadding': int(10 * self.scale_factor),  # Mysterious space between text and message layer
                'height': int(270 * self.scale_factor),
                'color': config['messageLayerColor'],
                'opacity': config['messageLayerOpacity'],
                'margin': {
                    'top': config['messageLayerMarginT'],
                    'left': config['messageLayerMarginL'],
                    'right': config['messageLayerMarginR'],
                    'bottom': config['messageLayerMarginB'],
                },
            },
            'glyph': {
                'size': 48 * self.scale_factor,
                'offset': 32 * self.scale_factor,
            },
        }
        definition_script = EXPORT_DEFAULT.OICE_DEFAULTS_SCRIPT % str(oice_defaults)

        with open(os.path.join(scenario_dir, '_definition.ks'), 'w') as file:
            file.write(definition_script)

        # Include interactions and handlers
        interaction_script = ''
        if self.is_offline:
            # Embed the script directly (For export)
            interaction_script += "[o2_iscript]%s[o2_endscript]\n" % EXPORT_DEFAULT.OICE_INTERACTION_SCRIPT
        else:
            # Retrieve the script through HTTP request
            interaction_script += '@oice_request param="type=interaction"\n'

        interaction_script += EXPORT_DEFAULT.KS_SCRIPT_RETURN

        with open(os.path.join(scenario_dir, '_interaction.ks'), 'w') as file:
            file.write(interaction_script)

        # Include all used macro
        macro_script = ""
        for macro in self.used_macro:
            if macro.content is None:
                continue
            macro_script += macro.content + "\n"

        macro_script += EXPORT_DEFAULT.KS_SCRIPT_RETURN

        with open(os.path.join(scenario_dir, '_macro.ks'), 'w') as file:
            file.write(macro_script)

        # Include used character configuration
        npcdata_script = self.export_used_character_config()

        with open(os.path.join(scenario_dir, '_npcdata.ks'), 'w') as file:
            file.write(npcdata_script)

        # Include used assets
        self.export_assets(data_dir)

        return project_dir

    def export(self):
        project_dir = self.create_novelspherejs_project_from_oice()

        subprocess.call(['zip', '-r', self.export_path, '.'], cwd=project_dir)
        shutil.rmtree(project_dir)


class KSScriptBuilder(ScriptExporter):

    def __init__(self, build_script, *args, **kwargs):
        self.build_script = build_script
        super(KSScriptBuilder, self).__init__(*args, **kwargs)

    def build(self):
        project_dir = super(KSScriptBuilder, self).create_novelspherejs_project_from_oice()

        subprocess.call([self.build_script, project_dir, self.export_path])
        shutil.rmtree(project_dir)

        # Add og meta into index.html
        index_html_path = os.path.join(self.export_path, "index.html")

        locale = self.oice.story.language
        image_url = self.og_image_button_url
        oice_image_url = self.og_image_origin_url  # for ios iframe background image
        og_url = self.oice_view_url
        description = self.oice.og_description

        processing_meta = False
        for line in fileinput.input(index_html_path, inplace=1):
            if line.startswith('<head>'):
                processing_meta = True
            elif processing_meta:
                print(EXPORT_DEFAULT.OICE_HTML_META % (
                    self.title, locale, self.title, description, og_url, image_url or oice_image_url, oice_image_url, og_url
                ))
                processing_meta = False
            print(line)

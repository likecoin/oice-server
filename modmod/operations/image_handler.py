import os
import logging
import subprocess
log = logging.getLogger(__name__)

settings = None

class ComposeOgImage(object):

    def __init__(self, uploaded_image_path):
        super().__init__()
        self.uploaded_image_path = uploaded_image_path

    def run(self):
        path = os.path.abspath(__file__)
        dir_path = os.path.dirname(path)

        og_image_handler_script = os.path.abspath(os.path.join(dir_path, '../scripts/og_image_handler.sh'))
        play_image_path =  os.path.abspath(os.path.join(dir_path, '..', 'res', 'og_play.png'))

        og_image_path = os.path.split(self.uploaded_image_path)[0]
        og_image_name = os.path.split(self.uploaded_image_path)[1]

        try:
            subprocess.run([og_image_handler_script, og_image_path, play_image_path, og_image_name])
        except Exception as e:
            log.error('falied here og_image_handler_script%s', e)
        else:
            log.debug('success here og_image_handler_script')

class ComposeCoverImage(object):

    def __init__(self, uploaded_image_path):
        super().__init__()
        self.uploaded_image_path = uploaded_image_path

    def run(self):
        path = os.path.abspath(__file__)
        dir_path = os.path.dirname(path)

        cover_image_handler_script = os.path.abspath(os.path.join(dir_path, '../scripts/cover_image_handler.sh'))
        play_image_path =  os.path.abspath(os.path.join(dir_path, '..', 'res', 'cover_play.png'))

        cover_image_path = os.path.split(self.uploaded_image_path)[0]
        cover_image_name = os.path.split(self.uploaded_image_path)[1]

        try:
            subprocess.run([cover_image_handler_script, cover_image_path, play_image_path, cover_image_name])
        except Exception as e:
            log.error('falied here cover_image_handler_script%s', e)
        else:
            log.debug('success here cover_image_handler_script')

class ResizeBackgroundImage(object):

    def __init__(self, uploaded_image_path):
        super().__init__()
        self.uploaded_image_path = uploaded_image_path

    def run(self):
        path = os.path.abspath(__file__)
        dir_path = os.path.dirname(path)

        background_image_handler_script = os.path.abspath(os.path.join(dir_path, '../scripts/background_image_handler.sh'))

        bg_image_path = os.path.split(self.uploaded_image_path)[0]
        bg_image_name = os.path.split(self.uploaded_image_path)[1]

        try:
            subprocess.run([background_image_handler_script, bg_image_path, bg_image_name])
        except Exception as e:
            log.error('falied here background_image_handler_script%s', e)
        else:
            log.debug('success here background_image_handler_script')

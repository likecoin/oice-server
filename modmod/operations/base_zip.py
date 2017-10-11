import os
import shutil
import tempfile
import pyramid_safile
import subprocess
import json
import re
import execjs
import logging
from modmod.exc import ValidationError
from execjs import ProgramError

from ..models import (
    DBSession,
    Character,
    CharacterQuery
)

log = logging.getLogger(__name__)

def read_config(config_path):

    if not os.path.exists(config_path):
        return None

    content = None
    with open(config_path, 'r') as fp:
        content = fp.read()

    return content


def read_npcdata(npcdata_path):

    if not os.path.exists(npcdata_path):
        return []

    with open(npcdata_path, 'r') as fp:
        content = fp.read()
        script_content = re.findall('\[o2_iscript\]([\s\S]*)\[o2_endscript\]',
                                    content)

        if (len(script_content) == 0):
            raise ValidationError("invalid npcdata.ks format")

        return script_content

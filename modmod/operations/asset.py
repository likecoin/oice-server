from ..models import (
    DBSession,
    Asset,
)
import transaction
import logging
import os
import subprocess
import shutil
import tempfile
import pyramid_safile
from modmod.exc import ValidationError

log = logging.getLogger(__name__)
def insert_asset(session, asset_to_insert, parent_asset):

    if parent_asset:
        insert_index = parent_asset.order+1
    else:
        insert_index = 1

    session.query(Asset) \
           .filter(
                Asset.library == asset_to_insert.library,
                Asset.order >= insert_index
            ) \
           .update(
                {Asset.order: Asset.order+1}
            )

    asset_to_insert.order = insert_index
    session.add(asset_to_insert)

def move_under(asset, new_parent_asset, session=DBSession):

    new_index = 1
    if new_parent_asset:
        new_index = new_parent_asset.order+1

        if asset.library != new_parent_asset.library:
            raise Exception('Source asset and parent asset are not in the same library')

    if asset.order > new_index:
        move_up(asset, new_index, session)
    elif asset.order < new_index:

        move_down(asset, new_index, session)

def move_up(asset, new_index, session=DBSession):

    if asset.order < new_index:
        raise 'Cannot move up, direction is not correct'
    elif asset.order == new_index:
        return

    session.query(Asset) \
           .filter(
                Asset.library_id == asset.library_id,
                Asset.order >= new_index,
                Asset.order < asset.order
            ) \
           .update(
                {Asset.order: Asset.order+1}
            )

    asset.order = new_index


def move_down(asset, new_index, session=DBSession):

    if asset.order > new_index:
        raise 'Cannot move down, direction is not correct'
    elif asset.order == new_index:
        return

    session.query(Asset) \
           .filter(
                Asset.library_id == asset.library_id,
                Asset.order > asset.order,
                Asset.order <= new_index
            ) \
           .update(
                {Asset.order: Asset.order-1}
            )

    asset.order = new_index


def delete_asset(session, asset):

    session.query(Asset) \
           .filter(
                Asset.library_id == asset.library_id,
                Asset.order > asset.order
            ) \
           .update(
                {Asset.order: Asset.order-1}
            )

    asset.is_deleted = True


def audio_transcodec(original_filename, fp):
    filename = os.path.splitext(original_filename)[0]
    tempdir = tempfile.mkdtemp()
    temp_zip = os.path.join(tempfile.mkdtemp(), filename + '.zip')

    fdst = open(os.path.join(tempdir, original_filename), 'wb+')
    shutil.copyfileobj(fp, fdst)

    subprocess.call(['ffmpeg', '-i', original_filename, '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', '-vn', '-sn', '-dn', filename + '.mp4'], cwd=tempdir)
    subprocess.call(['ffmpeg', '-i', original_filename, '-c:a', 'libvorbis', '-qscale:a', '5', '-vn', '-sn', '-dn', filename + '.ogg'], cwd=tempdir)
    os.remove(os.path.join(tempdir, original_filename))

    subprocess.call(['zip', '-r', temp_zip, '.'], cwd=tempdir)

    try:
        factory = pyramid_safile.get_factory()
        handle = factory.create_handle(os.path.basename(temp_zip), open(temp_zip, 'rb'))
        os.remove(temp_zip)
    except FileNotFoundError:
        raise ValidationError('ERR_AUDIO_TRANSCODE_FAILURE')
    else:
        subprocess.call(['unzip', '-o', handle.dst, '-d', os.path.dirname(handle.dst)])
    finally:
        shutil.rmtree(tempdir)

    return handle

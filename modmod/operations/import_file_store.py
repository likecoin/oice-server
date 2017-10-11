# pylama:ignore=W0401
import os
import pyramid_safile
from ..models import (
    DBSession,
    AssetType,
    Asset
)
from .script_import_model import *


class TemporaryAsset:

    def __init__(self, path, asset_types):
        self.path = path
        self.asset_types = asset_types
        self._asset = None

    @property
    def basename(self):
        return os.path.basename(self.path)

    @property
    def name_without_ext(self):
        return os.path.splitext(self.basename)[0]

    def add_asset_type(self, asset_type):
        if self._asset is not None:
            if asset_type not in self._asset.asset_types:
                self._asset.asset_types.append(asset_type)

    @property
    def asset(self):
        if self._asset is not None:
            return self._asset
        name = os.path.basename(self.path)
        factory = pyramid_safile.get_factory()
        handle = factory.create_handle(name, open(self.path, 'rb'))
        self._asset = Asset.from_handle(
            handle,
            asset_types=self.asset_types
        )
        self._asset.name = name
        self._asset.filename = name
        return self._asset


class ImportFileStore(object):

    def __init__(self, session, folder_path):
        self.session = session
        self.folder_path = folder_path
        self._asset_types = None
        self._asset_map = None
        self._assets = None
        self._errors = None

    # { folder_name: asset_type }
    @property
    def asset_types(self):
        if self._asset_types is None:
            self._asset_types = {}
            for type_ in DBSession.query(AssetType):
                self._asset_types[type_.folder_name.lower()] = type_
        return self._asset_types

    def asset_type_for_path(self, path):
        relative_path = os.path.relpath(path, self.folder_path)
        directory = relative_path.split(os.sep)[0].lower()
        return self.asset_types.get(directory)

    @property
    def assets(self):
        if self._assets is not None:
            return self._assets
        self._assets = []
        for root, path, name in folder_content(self.folder_path):
            asset_type = self.asset_type_for_path(path)
            if asset_type is None:
                continue

            temp_asset = TemporaryAsset(path, [asset_type])
            self._assets.append(temp_asset)
        return self._assets

    @property
    def asset_map(self):
        if self._asset_map is None:
            self._asset_map = {}
            for temp_asset in self.assets:
                name = temp_asset.name_without_ext.lower()
                self._asset_map[name] = temp_asset
        return self._asset_map

    def temp_asset_for_name(self, name_without_ext):
        return self.asset_map.get(name_without_ext)

    @property
    def errors(self):
        if self._errors is not None:
            return self._errors
        self._errors = []
        dirs = os.listdir(self.folder_path)
        for this_dir in dirs:
            if this_dir == "scenario":
                # ignore scenario as it is not asset
                continue
            if os.path.isdir(os.path.join(self.folder_path, this_dir)):
                if this_dir not in self.asset_types:
                    self._errors.append(
                        FolderNotSupportedImportResult(this_dir)
                    )
            else:
                self._errors.append(
                    FileAtRootImportedResult(this_dir)
                )
        return self._errors

'''Data Integration Processor (DIP) base elements'''

import abc
import collections
import dawgie
import os
import pathlib
import shutil
import typing
import yaml

from datetime import UTC, datetime


class Contaminable(abc.ABC):  # pylint: disable=too-few-public-methods
    @abc.abstractmethod
    def quarantine(self, location: pathlib.Path) -> typing.Self:
        '''Signal that this content should isolate when writable'''


class AuxillaryFile(Contaminable, dawgie.Value):
    def __init__(self):
        self._copy_tree = False
        self._feats = []
        self._name = None
        # bumped to 1.1.0: added _copy_tree attribute. Previously-pickled
        # instances from before this change are missing the attribute; the
        # version bump tells dawgie those cached values are stale so they
        # get recomputed rather than unpickled as-is.
        self._version_ = dawgie.VERSION(1, 1, 0)

    @property
    def copy_tree(self) -> bool:
        '''when True, name points at a directory tree to replicate wholesale

        Uses getattr with a default so any instance that slips through
        without the attribute set (e.g. an old cached value that somehow
        still gets unpickled) does not raise AttributeError.
        '''
        return getattr(self, '_copy_tree', False)

    @copy_tree.setter
    def copy_tree(self, flag: bool):
        self._copy_tree = bool(flag)

    @property
    def name(self) -> pathlib.Path:
        return self._name

    @name.setter
    def name(self, path: pathlib.Path):
        self._name = path

    def features(self):
        return self._feats

    def quarantine(self, location: pathlib.Path) -> typing.Self:
        '''move the contents to the quarenteen location

        The object returned is same class with the new location.
        '''
        result = self.__class__()
        result.copy_tree = self._copy_tree
        if self._name is not None:
            result.name = location / self._name.name
            for expanded in self._name.parent.glob(self._name.name):
                _safe_copy(expanded, location / expanded.name)
        return result


class Calibration(AuxillaryFile):
    pass


class Configuration(dawgie.Value):
    def __init__(self):
        self._version_ = dawgie.VERSION(1, 0, 0)
        self._content = None
        self._feats = []

    @property
    def name(self):
        return self._content

    @name.setter
    def name(self, value):
        self._content = value

    def features(self):
        return self._feats


class Cpgs(AuxillaryFile):
    pass


class Manifest(Contaminable, collections.UserList, dawgie.Value):
    def __init__(self, *args, **kwds):
        collections.UserList.__init__(self, *args, **kwds)
        self._version_ = dawgie.VERSION(1, 0, 0)
        self._feats = []
        self._at: str = 'unspecified'
        self._now = datetime.now(UTC)

    @property
    def at(self) -> str:
        return self._at

    @at.setter
    def at(self, location: str):
        self._at = location

    def deserialize(self, fn: str, clear: bool = True) -> typing.Self:
        '''load a manifest into this object

        It clears this manifest first, unless clear is False, the loads the
        file into this object. It returns itself for chaining.
        '''
        if clear:
            self.clear()
        with open(fn, 'rt', encoding='utf-8') as file:
            self.extend(yaml.safe_load(file))

    def features(self):
        return self._feats

    def quarantine(self, location: pathlib.Path) -> typing.Self:
        '''move the contents to the quarenteen location

        The manifest returned is with the new location.
        '''
        result = Manifest()
        for entry in self:
            result.append(location / entry.name)
            _safe_copy(entry, result[-1])
        return result

    def serialize(self, fn: str) -> typing.Self:
        '''write this manifest to a file'''
        with open(fn, 'tw', encoding='utf-8') as file:
            yaml.dump(list(str(fn) for fn in self), file)


class Recipe(AuxillaryFile):
    pass


def _safe_copy(src: pathlib.Path, dst: pathlib.Path):
    if os.access(src, os.R_OK) and not os.access(src, os.W_OK):
        dst.symlink_to(src)
    else:
        shutil.copy(src, dst)


def replicate_tree(src: pathlib.Path, dst_root: pathlib.Path):
    '''replicate the directory tree at src into dst_root

    dst_root is the destination base; the tree is placed at
    dst_root / src.name so the source subdirectory name is preserved (e.g. a
    src of .../calspec_data lands at dst_root/calspec_data). Each file is
    link-or-copied via _safe_copy: read-only sources are symlinked, writable
    sources are copied. Directory structure is recreated with mkdir.
    '''
    src = pathlib.Path(src)
    dst = pathlib.Path(dst_root) / src.name
    for dirpath, _dirnames, filenames in os.walk(src):
        rel = pathlib.Path(dirpath).relative_to(src)
        (dst / rel).mkdir(parents=True, exist_ok=True)
        for filename in filenames:
            target = dst / rel / filename
            if not target.exists():
                _safe_copy(pathlib.Path(dirpath) / filename, target)

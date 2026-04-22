'''Data Integration Processor (DIP) base elements'''

import abc
import collections
import dawgie
import os
import pathlib
import shutil
import typing
import yaml


class Contaminable(abc.ABC):  # pylint: disable=too-few-public-methods
    @abc.abstractmethod
    def quarantine(self, location: pathlib.Path) -> typing.Self:
        '''Signal that this content should isolate when writable'''


class AuxillaryFile(Contaminable, dawgie.Value):
    def __init__(self):
        self._feats = []
        self._name = None
        self._version_ = dawgie.VERSION(1, 0, 0)

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
        if self._name is not None:
            result.name =  location / self._name.name
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

'''The intermediate form of the DSL'''

import inspect
import logging
import typing

from . import Kind
from .template import CODE_BLOCKS
from string import Template

LOG = logging.getLogger(__name__)


class Class:
    def __init__(self, declaration: str, name: str, fsm: str = ''):
        self._clsdef: str = '.'.join(declaration.split('.')[-2:])
        self._contents: set[typing.Self] = set()
        self._fsmdef: str = fsm
        self._location: str = declaration[: -len(self._clsdef) - 1]
        self._name: str = name

    def __repr__(self):
        return '\n'.join(self._strings())

    def __str__(self):
        return '\n'.join(self._strings())

    def _strings(self, indent: str = '') -> str:
        result = [indent + f'{self._name}: {self._location}.{self._clsdef}']
        for cls in self._contents:
            # pylint:disable=protected-access
            result.extend(cls._strings(indent + '  '))
        return result

    @property
    def definition(self) -> str:
        '''direct definition of the class like Alg(dawgie.Algorithm)'''
        return self._clsdef

    @property
    def contents(self) -> set[typing.Self]:
        '''classes whose instances this class holds'''
        return self._contents

    @property
    def fsm_class(self) -> str:
        return self._fsmdef.split('.')[-1]

    @property
    def fsm_path(self) -> str:
        return '.'.join(self._fsmdef.split('.')[:-1])

    @property
    def location(self) -> str:
        '''the pythonic location (package...module) like a.b.c'''
        return self._location if self._location else '.'

    @property
    def myname(self) -> str:
        '''the last part of the name like cat from l1.cat'''
        return self._name.split('.')[-1]

    @property
    def name(self) -> str:
        '''the dawgie name of this class like task.alg.svn.val'''
        return self._name

    @property
    def val_class(self) -> str:
        return self._fsmdef.split('.')[-1]

    @property
    def val_path(self) -> str:
        return '.'.join(self._fsmdef.split('.')[:-1])

    def asdict(self) -> dict[str, str]:
        '''turn it into a dictionary'''
        properties = {
            f'cls_{name}': getattr(self, name)
            for name, value in inspect.getmembers(self.__class__)
            if isinstance(value, property)
        }
        return dict(
            (k, v)
            for k, v in filter(
                lambda t: isinstance(t[1], str), properties.items()
            )
        )

    def kind(self) -> Kind:
        '''return the type of class that this represents'''
        for k in Kind:
            if k.value in self._clsdef:
                return k
        raise ValueError(
            f'Unknown class definition "{self._clsdef}". '
            'Please extend this class.'
        )


class Module:
    def __init__(self, name):
        self._classes = []
        self._imports = set()
        self._name = name

    @property
    def classes(self) -> [str]:
        return self._classes

    @property
    def imports(self) -> set[str]:
        return self._imports

    @property
    def myname(self) -> str:
        return self._name.split('.')[-1]

    @property
    def name(self) -> str:
        return self._name


class Package:
    def __init__(self, name: str, placeholders: bool):
        self._modules: [Module] = []
        self._name: str = name
        self._packages: {str: typing.Self} = {}
        self._wtfp: bool = placeholders

    @property
    def modules(self) -> [Module]:
        return self._modules

    @property
    def name(self) -> str:
        return self._name

    @property
    def packages(self) -> {str: typing.Self}:
        return self._packages

    @property
    def write_task_factory_placeholders(self) -> bool:
        return self._wtfp


def _update_run(cls: Class, template: Template) -> [set[str], Template]:
    imports = {'dawgie', 'dawgie.util', 'dip.base'}
    item_init = []
    item_list = []
    for sv in filter(lambda c: c.kind() == Kind.STATE_VECTOR, cls.contents):
        svc = sv.definition.split('(')[0]
        svn = f'self._{sv.myname}'
        svl = '' if sv.location == '.' else sv.location
        if svl:
            imports.add(svl)
            svc = f'{svl}.{svc}'
        item_init.append(f'        {svn} = {svc}()')
        item_list.append(svn)
    template = Template(
        template.safe_substitute(
            svs_init='\n'.join(item_init), svs_list=','.join(item_list)
        )
    )
    item_init.clear()
    item_list.clear()
    for vref in filter(lambda c: c.kind() == Kind.V_REF, cls.contents):
        svn, feat = vref.name.split('.')[2:]
        src = vref.contents.pop()
        cls = src.definition.split('(')[0]
        imports.add(src.location)
        tloc = '.'.join(src.location.split('.')[:2])
        imports.add(tloc)
        match src.kind():
            case Kind.ALGORITHM:
                tloc += '.task'
            case Kind.ANALYZER:
                tloc += '.analysis'
            case Kind.REGRESSION:
                tloc += '.regress'
            case _:
                LOG.error('Non-runnable for V_REF')
        item_init.append(f'        self._{src.myname} = {src.location}.{cls}()')
        item_list.append(
            f'dawgie.V_REF({tloc}, self._{src.myname}, '
            f'self._{src.myname}.sv_as_dict()["{svn}"], "{feat}")'
        )
    template = Template(
        template.safe_substitute(
            vrefs_init='\n'.join(item_init), vrefs_list=','.join(item_list)
        )
    )
    return imports, template


def _update_sv(cls: Class, template: Template) -> [set[str], Template]:
    imports = {'dawgie'}
    vals = []
    for val in filter(lambda c: c.kind() == Kind.VALUE, cls.contents):
        vn = val.myname
        vc = val.val_class
        if val.val_path:
            imports.add(val.val_path)
            vc = f'{val.val_path}.{val.val_class}'
        vals.append(f'        self["{vn}"] = {vc}()')
    vals.sort()
    template = Template(template.safe_substitute(values='\n'.join(vals)))
    return imports, template


def add(cls: Class, mod: Module):
    k = cls.kind()
    match (k):
        case Kind.ALGORITHM | Kind.ANALYZER | Kind.REGRESSION:
            imports, template = _update_run(cls, CODE_BLOCKS[k])
        case Kind.STATE_VECTOR:
            imports, template = _update_sv(cls, CODE_BLOCKS[k])
        case Kind.VALUE | Kind.V_REF:
            # VALUE is handled in _update_sv
            # V_REF is handled in _update_alg
            imports = set()
            template = Template('')
        case _:
            LOG.critical('Do not understand %s. Please extend my abilities', k)
            return
    mod.imports.update(imports)
    if template.template.strip():
        mod.classes.append(template.safe_substitute(**cls.asdict()))

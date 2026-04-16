'''separate out the mechanics of writing content'''

import logging
import pathlib
import string

from . import BEGIN, END, model

LOG = logging.getLogger(__name__)
PLACEHOLDERS = '''
# pylint: disable=duplicate-code

def analysis(
    prefix: str, ps_hint: int = 0, runid: int = -1
) -> dawgie.FactoryPlaceholder[dawgie.base.Analysis]:
    raise NotImplementedError('placeholder until dawgie monkey patches me')


def events() -> dawgie.FactoryPlaceholder[list[dawgie.EVENT]]:
    raise NotImplementedError('placeholder until dawgie monkey patches me')


def regress(
    prefix: str, ps_hint: int = 0, target: str = '__none__'
) -> dawgie.FactoryPlaceholder[dawgie.base.Regress]:
    raise NotImplementedError('placeholder until dawgie monkey patches me')


def task(
    prefix: str, ps_hint: int = 0, runid: int = -1, target: str = '__none__'
) -> dawgie.FactoryPlaceholder[dawgie.base.Task]:
    raise NotImplementedError('placeholder until dawgie monkey patches me')

# pylint: enable=duplicate-code
'''


def author_placeholders(path: pathlib.Path):
    '''put the placeholders in the package defined by path'''
    content = f'''
"""auto generated"""

import dawgie
import dawgie.base

{BEGIN}
{END}
    '''
    fn = path / '__init__.py'
    if fn.is_file():
        with fn.open(mode='rt', encoding='utf-8') as file:
            content = file.read()
    if BEGIN not in content or END not in content:
        LOG.error(
            'The file %s has content but does not have a generator area. '
            'Cowardly doing nothing!',
            fn,
        )
        return
    if content.count(BEGIN) > 1 or content.count(END) > 1:
        LOG.error(
            'The file %s has too many generator areas. '
            'Cowardly doing nothing!',
            fn,
        )
        return
    finish = content.find(BEGIN) + len(BEGIN)
    restart = content.find(END)
    content = content[: finish + 1] + PLACEHOLDERS + content[restart:]
    with fn.open(mode='tw', encoding='utf-8') as file:
        file.write(content)


def author_module(module: model.Module, path: pathlib.Path, version: str):
    '''write the module to the package defined by path'''
    content = '# pylint: disable=duplicate-code\n\n'
    fn = path / f'{module.myname}.py'
    content += '\n'.join(
        f'import {m}' for m in sorted(module.imports, key=str.casefold)
    )
    content += '\n'.join(module.classes)
    content = string.Template(content).safe_substitute(version=version)
    if 'auto' not in path.parts and fn.is_file():
        hold = content + '\n# pylint: enable=duplicate-code\n'
        with fn.open(mode='rt', encoding='utf-8') as file:
            content = file.read()
        if BEGIN not in content or END not in content:
            LOG.error(
                'The file %s has content but does not have a generator area. '
                'Cowardly doing nothing!',
                fn,
            )
            return
        if content.count(BEGIN) > 1 or content.count(END) > 1:
            LOG.error(
                'The file %s has too many generator areas. '
                'Cowardly doing nothing!',
                fn,
            )
            return
        finish = content.find(BEGIN) + len(BEGIN)
        restart = content.find(END)
        content = content[: finish + 1] + hold + content[restart:]
    else:
        content = '"""auto generated"""\n\n' + content
    with fn.open(mode='tw', encoding='utf-8') as file:
        file.write(content)

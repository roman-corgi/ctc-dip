'''Use the model to produce code'''

import logging
import pathlib

from . import model, writer

LOG = logging.getLogger(__name__)


def containerize(
    distillate: [model.Class],
    bottles: dict[str, model.Module] = None,
    parent: str = '',
) -> {str: model.Module}:
    '''turn the distillates into objects that will serialize into code'''
    if not bottles:
        bottles = {}
        LOG.info('start recursive decent into the distillate for bottling')
    for cls in distillate:
        location = parent if cls.location == '.' else cls.location
        if not location:
            LOG.error(
                'The locations is "%s" and the parent location is "%s".',
                cls.location,
                parent,
            )
            return bottles
        if location not in bottles:
            bottles[location] = model.Module(location)
        model.add(cls, bottles[location])
        containerize(cls.contents, bottles, location)
    return bottles


def deliver(pallets: {str: model.Package}, root: pathlib.Path, version: str):
    '''serialize the model to code in self building order'''
    LOG.info(
        'recursive decent to deliver pallets (write package/modules to disk)'
    )
    for pkg in pallets.values():
        path = root / pkg.name
        if not path.is_dir():
            if path.exists():
                LOG.error(
                    'The path %s exists but is not a directory (package)', path
                )
                return
            path.mkdir(parents=True, exist_ok=True)
        if pkg.write_task_factory_placeholders:
            writer.author_placeholders(path)
        fn = path / '__init__.py'
        if not fn.is_file():
            fn.touch()
        for module in pkg.modules:
            writer.author_module(module, path, version)
        deliver(pkg.packages, path, version)


def unitize(bottles: {str: model.Module}) -> {str: model.Package}:
    '''organize model from top package to lowest method/function'''
    pallets = {}
    LOG.info('build pallets to be distributed (modules to packages)')
    for modname, mod in bottles.items():
        pkgs = pallets
        for idx, pkgname in enumerate(modname.split('.')[:-1]):
            if pkgname not in pkgs:
                pkgs[pkgname] = model.Package(pkgname, idx == 1)
            last = pkgs[pkgname]
            pkgs = last.packages
        last.modules.append(mod)
    return pallets

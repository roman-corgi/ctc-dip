'''Distill a GraphViz file to a structure that can be used to write code'''

import collections.abc
import functools
import logging
import pathlib
import pydot
import typing

from . import ALL_KEYWORDS, KEYWORDS, Kind, model

LOG = logging.getLogger(__name__)

type CollisionData = collections.abc.Iterator[tuple[str, str, str, str]]


def _add_missing_svs(tree: {}):
    keys = set(_flatten(tree))
    svns = set(
        '.'.join(k.split('.')[:3])
        for k in filter(lambda s: s.count('.') > 2, keys)
    )
    for svn in svns:
        content = _content(svn, tree)
        if svn not in content.values():
            csv = svn.split('.')[-1]
            csv = ''.join(s.capitalize() for s in csv.split('_'))
            content[f'.{csv}StateVector(dawgie.StateVector)'] = svn


def _content(flatname: str, tree: {}) -> {}:
    if 'nested_dicts' in tree:
        tree = tree['nested_dicts']
    for name in flatname.split('.'):
        tree = tree[name]
    return tree['__content__']


def _do_edge(edge: pydot.Edge) -> bool:
    return 'style' not in edge.get_attributes() or (
        _getattr(edge, 'style').lower() != 'dashed'  # means virtual
        and _getattr(edge, 'style').lower() != 'dotted'  # means WIP
    )


def _flatten(nested: dict[str, typing.Any], path: str = ''):
    keys = []
    for k, v in nested.items():
        if k == '__content__':
            continue
        fullpath = f'{path}.{k}' if path else k
        if '__content__' in v and v['__content__']:
            keys.append(fullpath)
        keys.extend(_flatten(v, fullpath))
    return keys


def _galg(node, vapors):
    names = _getattr(node, 'runname').split('.')
    cn = f'dip.{names[0]}.auto.{names[1]}.Runnable({_getattr(node, "runtype")})'
    _insert(names, vapors)
    old = functools.reduce(_lam, names, vapors)['__content__']
    new = {
        cn: (
            _getattr(node, 'runname'),
            _getattr(node, 'fsmtype'),
        )
    }
    return old, new


def _getattr(node, key):
    return node.get_attributes()[key].strip('"')


def _insert(names, vapors):
    loc = vapors
    for name in names:
        if name not in loc:
            loc[name] = {}
            loc[name]['__content__'] = {}
        loc = loc[name]


def _is_enhanced(node: pydot.Node) -> bool:
    return any(k in node.get_attributes() for k in ALL_KEYWORDS)


def _lam(d, key):
    return d[key]


def _merge_with_side_effects(
    source: dict[str, typing.Any],
    sink: dict[str, typing.Any],
    path: str = '',
) -> CollisionData:
    '''
    INTERNAL USE ONLY. Recursively merges source into sink (in-place).

    WARNING: This is a mutating generator. The 'sink' dict is modified
    as iteration proceeds. It must be fully consumed to ensure the
    merge is completed.

    Yields:
        The dot-notation path of keys that collided within '__content__'.
    '''
    for key, value in source.items():
        current_path = f'{path}.{key}' if path else key
        if key not in sink:
            sink[key] = value
            continue
        if key == '__content__':
            for sub_key, sub_val in value.items():
                if sub_key in sink[key] and sub_val != sink[key][sub_key]:
                    yield current_path, sub_key, sub_val, sink[key][sub_key]
                else:
                    sink[key][sub_key] = sub_val
        else:
            yield from _merge_with_side_effects(value, sink[key], current_path)


def _sv(node, typ, vapors):
    names = _getattr(node, 'svname').split('.')
    _insert(names, vapors)
    old = functools.reduce(_lam, names, vapors)['__content__']
    new = {_getattr(node, 'clsname') + f'({typ})': (_getattr(node, 'svname'),)}
    return old, new


def _val(graph, node, vapors):
    names = _getattr(node, 'valname').split('.')
    vrefs = set()
    _insert(names, vapors)
    for edge in graph.get_edges():
        if edge.get_source() == node.get_name():
            vrefs.add(
                _getattr(graph.get_node(edge.get_destination())[0], 'runname')
            )
    old = functools.reduce(_lam, names, vapors)['__content__']
    new = {'dawgie.Value': (vrefs - {None}, _getattr(node, 'valtype'))}
    return old, new


def collection(condensate: {}):  # pylint: disable=too-many-locals
    '''collect all the nested dictionaries into containers'''
    runnables = []
    # pylint: disable=too-many-nested-blocks
    for runnable in filter(
        lambda s: s.count('.') == 1, condensate['flat_keys']
    ):
        for clsdef, needed in _content(runnable, condensate).items():
            runnables.append(model.Class(clsdef, runnable, needed[1]))
            for svn in filter(
                lambda s, S=runnable + '.': s.startswith(S)
                and s.count('.') == 2,
                condensate['flat_keys'],
            ):
                for svndef in _content(svn, condensate):
                    sv = model.Class(svndef, svn)
                    runnables[-1].contents.add(sv)
                    for val in filter(
                        lambda s, S=svn + '.': s.startswith(S)
                        and s.count('.') == 3,
                        condensate['flat_keys'],
                    ):
                        for valdef, needed in _content(val, condensate).items():
                            sv.contents.add(model.Class(valdef, val, needed[1]))
    for valname in filter(lambda s: s.count('.') == 3, condensate['flat_keys']):
        vrn = '.'.join(valname.split('.')[:2])
        vrun = [r for r in runnables if r.name == vrn][0]
        for vrefs, _ in _content(valname, condensate).values():
            for vref in vrefs:
                run = [r for r in runnables if r.name == vref]
                if len(run) != 1:
                    LOG.error(
                        'The runnable %s that value %s points at does '
                        'not exist',
                        vref,
                        valname,
                    )
                else:
                    vcls = model.Class('dawgie.V_REF', valname)
                    vcls.contents.add(vrun)
                    run[0].contents.add(vcls)
    return runnables


def condense(vapors: {}) -> {}:
    '''merge all dot file DSL content into a single tree'''
    merged = {}
    LOG.info('Merging all dot file DSL information into one tree')
    for dot, content in vapors.items():
        if not content:
            LOG.info('nothing of interest was found in %s', dot.name)
            continue
        for path, item, cval, pval in _merge_with_side_effects(content, merged):
            LOG.error(
                'The definition %s for %s at %s in dot file %s conflicts with previous definition %s',
                cval,
                item,
                path,
                dot.name,
                pval,
            )
    _add_missing_svs(merged)
    keys = _flatten(merged)
    runs = set(k for k in filter(lambda s: s.count('.') == 1, keys))
    LOG.info('Checking all algorithms/analyzers/regressions for data flow')
    for r in sorted(runs):
        if not any(
            k.startswith(r) for k in filter(lambda s: s.count('.') > 1, keys)
        ):
            LOG.error(
                'The algorithm/analyzer/regression %s has no data flow', r
            )
    LOG.info(
        'Checking all data elements flow to/from algorithms/analyzers/regressions'
    )
    for k in sorted(filter(lambda s: s.count('.') > 2, keys)):
        if '.'.join(k.split('.')[:2]) not in runs:
            LOG.error(
                'Data element %s does not flow to any algorithm/analyzer/regression',
                k,
            )
    return {'flat_keys': keys, 'nested_dicts': merged}


def mashing(grains: {pathlib.Path: pydot.Dot}) -> pydot.Dot:
    '''merge all of the dot files into one graph'''
    edges = set()
    result = pydot.Dot(graph_type='digraph')
    for dot, graph in grains.items():
        for node in filter(_is_enhanced, graph.get_nodes()):
            if not result.get_node(node.get_name()):
                result.add_node(node)
                node.set('filename', dot.name)
            else:
                LOG.error(
                    'The dot file %s contains the enhanced node %s as '
                    'does the dot file %s. Keeping the former and '
                    'tossing the latter.',
                    _getattr(result.get_node(node.get_name()), 'filename'),
                    node.get_name(),
                    dot.name,
                )
        for edge in filter(_do_edge, graph.get_edges()):
            name = f'{edge.get_source()}->{edge.get_destination()}'
            if name not in edges:
                edges.add(name)
                result.add_edge(edge)
    for edge in edges:
        src, dst = edge.split('->')
        if not result.get_node(src):
            LOG.error('Missing node %s', src)
        if not result.get_node(dst):
            LOG.error('Missing node %s', dst)
    return result


def vaporize(mash: pydot.Dot):
    '''read the mega GraphViz graph extracting meaningful nodes to transmutation

    see dip.basis.transmute for DSL details.
    '''
    result = {}
    # pylint: disable=too-many-nested-blocks
    for node in mash.get_nodes():
        for typ, names in KEYWORDS.items():
            matches = [name in node.get_attributes() for name in names]
            if all(matches):
                LOG.info('found %s in %s', typ, node.get_name())
                match typ:
                    case Kind.ALGORITHM | Kind.ANALYZER | Kind.REGRESSION:
                        old, new = _galg(node, result)
                    case Kind.STATE_VECTOR:
                        old, new = _sv(node, typ, result)
                    case Kind.VALUE:
                        old, new = _val(mash, node, result)
                    case _:
                        LOG.critical(
                            'Do not understand %s. Please extend my abilities',
                            typ,
                        )
                        break
                for k, v in new.items():
                    if k in old:
                        if v == old[k]:
                            LOG.warning(
                                'Duplicate node %s in dot file %s.',
                                node.get_name(),
                                _getattr(node, 'filename'),
                            )
                        else:
                            LOG.error(
                                '2 nodes with content %s in dot file %s.',
                                k,
                                _getattr(node, 'filename'),
                            )
                            break
                old.update(new)
                break
            if any(matches):
                LOG.warning(
                    'the node %s in dot file %s does not supply all of '
                    'the keywords %s for %s',
                    node.get_name(),
                    _getattr(node, 'filename'),
                    str(names),
                    typ,
                )
    return {'uber graph': result}


def wash(dots: [pathlib.Path]) -> {pathlib.Path: pydot.Dot}:
    '''find only the dot files with DSL content'''
    result = {}
    for dot in dots:
        if dot.is_file():
            LOG.info('mashing %s', dot.name)
            try:
                graph = pydot.graph_from_dot_file(dot.resolve())[0]
                nodes = list(filter(_is_enhanced, graph.get_nodes()))
                if not nodes:
                    continue  # no keywords so not part of the DSL
                result[dot] = graph
            except:  # noqa: E722 # pylint: disable=bare-except
                LOG.exception('Cannot process %s as GraphViz file', dot.name)
        else:
            LOG.error('%s does not appear to be a file', dot.resolve())
    return result

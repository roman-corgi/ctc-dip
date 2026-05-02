#! /usr/bin/env python
'''add (bloat) graphviz files based on abs_design to include dawgie tie-in'''

import argparse
import pydot

from pathlib import Path


def _multiplexer(node: pydot.Node) -> str:
    if 'runname' not in node.get_attributes():
        lvl, ch, cht, dm = node.get_name().split('_')
        ch = f'{ch}_{cht}'
        if dm == 'demux':
            if not lvl.endswith('a'):
                lvl += 'a'
            node.set('runname', f'{lvl}.{dm}_{ch}')
            node.set('runtype', 'dawgie.Algorithm')
            node.set('fsmtype', 'dip.clerk.impls.demux.FSM')
        if dm == 'mux':
            if not lvl.endswith('b'):
                lvl += 'b'
            node.set('runname', f'{lvl}.{dm}_{ch}')
            node.set('runtype', 'dawgie.Analyzer')
            node.set('fsmtype', 'dip.clerk.impls.mux.FSM')


def _output(graph: pydot.Dot, node: pydot.Node):
    name = node.get_name()
    shape = '' if node.get_shape() is None else node.get_shape().strip('"')
    source = None
    if shape == 'ellipse':
        for edge in graph.get_edges():
            if edge.get_destination().strip() == name:
                if source is not None:
                    raise ValueError(
                        f'more than one edge uses {name} as a destination'
                    )
                source = graph.get_node(edge.get_source())[0]
    return source


def _process(graph: pydot.Dot, node: pydot.Node):
    name = node.get_name()
    if name.startswith('trans_'):
        _transmute(node)
    elif name.split('_')[-1] in ['demux', 'mux'] and '_man_' not in name:
        _multiplexer(node)
    else:
        src = _output(graph, node)
        if src:
            if 'runname' not in src.get_attributes():
                _process(graph, src)
            _product(node, src)


def _product(node: pydot.Node, src: pydot.Node):
    if 'valname' not in node.get_attributes():
        name = node.get_name()
        typ = (name + '_ignore').split('_')[3]
        if typ == 'man':
            pr = src.get('runname').strip('"')
            node.set('valname', f'{pr}.product.manifest')
            node.set('valtype', 'dip.base.Manifest')


def _transmute(node: pydot.Node):
    if 'runname' not in node.get_attributes():
        ch, cht, bl, el = node.get_name().split('_')[1:]
        ch = f'{ch}_{cht}'
        node.set('runname', f'{bl}.transmutation_{ch}')
        node.set('runtype', 'dawgie.Algorithm')
        node.set('fsmtype', 'dip.base.Runner')


def _valid_file(arg: str) -> Path:
    p = Path(arg)
    if not p.is_file():
        raise argparse.ArgumentTypeError(f"'{arg}' is not a valid file.")
    return p


def bloat(channels: [Path]):
    for channel in channels:
        graph = pydot.graph_from_dot_file(channel.resolve())[0]
        for node in graph.get_nodes():
            _process(graph, node)
        graph.write(channel.resolve())


def cli():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "channels",
        nargs="+",
        type=_valid_file,
        help='list of channel file names',
    )
    args = ap.parse_args()
    bloat(args.channels)


if __name__ == '__main__':
    cli()

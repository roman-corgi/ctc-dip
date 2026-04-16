'''run transmute

This modules exists to
  - support mechanism `python -m dip.basis.transmute`
  - define the arguments needed to control the transmutation
  - verify valid arguments
  - interpret and convert the arguments from the CLI to a python object
'''

import argparse
import logging
import sys

from . import distill
from . import logistics
from pathlib import Path

from pprint import pprint

LOG = logging.getLogger('dip.basis.transmute')


# pylint: disable=too-few-public-methods
class LoggingNameFilter(logging.Filter):
    def filter(self, record):
        index = min([record.name.count('.'), 2])
        record.short_name = '.'.join(record.name.split('.')[index:])
        return True


# pylint: enable=too-few-public-methods


def main():
    ap = argparse.ArgumentParser(
        description='Transmute the basis to concrete through code generation '
        'from the GraphViz files acting as a Domain Specific Language (DSL).',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    known = list(Path(__file__).parent.parent.glob('*.dot'))
    levels = [logging.ERROR, logging.WARNING, logging.INFO]
    ap.add_argument(
        'dots',
        default=known,
        nargs='*',
        type=Path,
        help='list of GraphViz dot files to distill. Will use dip/basis/*.dot '
        'if none are provided.',
    )
    ap.add_argument(
        '-O',
        '--outdir',
        default=Path(__file__).parent.parent.parent.parent,
        type=Path,
        help='the root/repo directory to generate code. It should contain or '
        'will contain the directory dip.',
    )
    ap.add_argument(
        '-v',
        '--verbose',
        action='count',
        help='increse verbosity (none=ERROR, -v=WARNING, -vv=INFO)',
    )
    ap.add_argument(
        '--version',
        default='0, 0, 0',
        help='the dawgie.VERSION args to set during code generation. '
        'Use the project.toml file to set the DIP version. '
        'NOTE the , not the .',
    )
    args = ap.parse_args()
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(LoggingNameFilter())
    logging.basicConfig(
        level=levels[min(2, args.verbose)],
        format="%(levelname)s : %(short_name)s.%(funcName)s : %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        handlers=[handler],
    )
    grains = distill.wash(args.dots)
    if args.verbose > 2:
        print('Grains:')
        pprint(grains, indent=2)
    mash = distill.mashing(grains)
    if args.verbose > 2:
        print('\n\nMash:')
        pprint(mash, indent=2)
    vapors = distill.vaporize(mash)
    if args.verbose > 2:
        print('\n\nVapors:')
        pprint(vapors, indent=2)
    condensate = distill.condense(vapors)
    if args.verbose > 2:
        print('\n\nCondensate:')
        pprint(condensate, indent=2)
    distillate = distill.collection(condensate)
    if args.verbose > 2:
        print('\n\nDistillate:')
        pprint(distillate, indent=2)
    bottles = logistics.containerize(distillate)
    if args.verbose > 2:
        print('\n\nBottles:')
        pprint(bottles, indent=2)
    pallets = logistics.unitize(bottles)
    if args.verbose > 2:
        print('\n\nPallets:')
        pprint(pallets, indent=2)
    logistics.deliver(pallets, args.outdir, args.version)


if __name__ == '__main__':
    main()

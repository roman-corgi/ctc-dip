'''define the hard bits of categorization'''

import dawgie
import dip.base
import dip.bindings.categorization
import logging
import shutil

from astropy.io import fits
from dip.binding_help import get_tag
from dip.bindings.categorization import operand_type, logical_operator
from pathlib import Path

from . import util

LOG = logging.getLogger(__name__)


class FSM(dip.base.Orchestrator):
    # pylint: disable=too-many-branches,too-many-return-statements
    @staticmethod
    def _apply(commands, fn, tagname):
        if commands is None or not commands.orderedContent():
            return False
        if not fn.is_file():
            LOG.error('The file %s does not exist or is not a real file', fn)
            return False
        result = []
        with fits.open(fn) as hdus:
            hdr = {}
            for hdu in hdus:
                hdr.update(hdu.header)
            for cmd in commands.orderedContent():
                command = cmd.value
                if isinstance(command, operand_type):
                    val = hdr[command.keyword]
                    cast = FSM._caster(val)
                    vals = [
                        cast(v.orderedContent()[0].value)
                        for v in command.value_
                    ]
                    r = getattr(Operands, command.operator.replace('-', '_'))(
                        val, vals
                    )
                    LOG.info(
                        'Keyword %s = "%s" and results in %s against %s',
                        command.keyword,
                        val,
                        r,
                        vals,
                    )
                    result.append(not r if command.not_ else r)
                elif isinstance(command, logical_operator):
                    if len(result) < 2:
                        LOG.error(
                            'Stack underflow in %s. Requesting operation %s '
                            'with less than two values in the stack.',
                            tagname,
                            str(command),
                        )
                        return False
                    a = result.pop()
                    b = result.pop()
                    match command.lower():
                        case 'and':
                            result.append(a and b)
                        case 'nand':
                            result.append(not (a and b))
                        case 'nor':
                            result.append(not (a or b))
                        case 'or':
                            result.append(a or b)
                        case 'xnor':
                            result.append(a == b)
                        case 'xor':
                            result.append(a != b)
                        case _:
                            LOG.error(
                                'do not know this logical operation %s',
                                str(command),
                            )
                            return False
                else:
                    LOG.error('What?? RPN only has operands and operators')
                    return False
            if len(result) != 1:
                LOG.error(
                    'RPN stack %s should result in a single value but have %d',
                    tagname,
                    len(result),
                )
                return False
        return result[0]

    # pylint: enable=too-many-branches,too-many-return-statements

    @staticmethod
    def _caster(val):
        for typ in [bool, complex, float, int]:
            if isinstance(val, typ):
                return typ
        return str

    def _collate(self, categories, manifest) -> dip.base.ProductStatus:
        for l1 in manifest:
            l1 = Path(l1)
            channels = []
            for channelname in filter(
                lambda s: s != 'unk', self.outputs['channel']
            ):
                channel = get_tag(categories, channelname)
                if FSM._apply(channel, l1, channelname):
                    channels.append(channelname)
            if channels:
                if len(channels) > 1:
                    LOG.error(
                        'L1 file %s matches more than 1 channel %s. '
                        'Adding to UNK.',
                        l1,
                        channels,
                    )
                    self.outputs['channel']['unk'].append(l1)
                else:
                    self.outputs['channel'][channels[0]].append(l1)
            else:
                self.outputs['channel']['unk'].append(l1)
        LOG.info('output: %s', str(self.outputs['channel']))
        return dip.base.ProductStatus.ALL

    def _do_delegation(self):
        xml = self._load('categorization.xml')
        categories = dip.bindings.categorization.CreateFromDocument(xml)
        xml = self._load('system.xml')
        system = dip.bindings.system.CreateFromDocument(xml)
        journal = Path(system.journal.location)
        staging = Path(system.staging.location)
        manifest = dip.base.Manifest()
        manifest.at = self.dawgie_name
        mfn = staging / util.tn2l1mfn(self.target)
        if not mfn.is_file():
            mfn = staging / mfn.name.lower()
        if not mfn.is_file():
            raise dawgie.NoValidInputDataError(
                f'No manifest file matches target name {self.target}'
            )
        manifest.deserialize(mfn)
        shutil.move(mfn, journal / mfn.name)
        return self._collate(categories, manifest)


class Operands:
    @staticmethod
    def contains_all(val, vals):
        vl = val.split(',') if isinstance(val, str) else [val]
        return all(v in vl for v in vals)

    @staticmethod
    def contains_any(val, vals):
        vl = val.split(',') if isinstance(val, str) else [val]
        return any(v in vl for v in vals)

    @staticmethod
    def equals_all(val, vals):
        return all(val == v for v in vals)

    @staticmethod
    def equals_any(val, vals):
        return any(val == v for v in vals)

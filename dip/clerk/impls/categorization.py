'''define the hard bits of categorization'''

import dawgie
import dip.base
import dip.bindings.categorization
import logging
import shutil

from astropy.io import fits
from dip.binding_help import get_tag
from pathlib import Path

from . import util

LOG = logging.getLogger(__name__)


class FSM(dip.base.Orchestrator):
    @staticmethod
    def _apply(rules, fn):
        if rules is None:
            return False
        if not fn.is_file():
            LOG.error('The file %s does not exist or is not a real file', fn)
            return False
        result = None
        with fits.open(fn) as hdus:
            hdr = {}
            for hdu in hdus:
                hdr.update(hdu.header)
            for rule in rules:
                val = hdr[rule.keyword]
                cast = FSM._caster(val)
                vals = [
                    cast(v.orderedContent()[0].value)
                    for v in get_tag(rule, 'value')
                ]
                r = getattr(Operands, rule.operator.replace('-', '_'))(
                    val, vals
                )
                LOG.info(
                    'Keyword %s = "%s" and results in %s against %s',
                    rule.keyword,
                    val,
                    r,
                    vals,
                )
                if result is None:
                    result = r
                match rule.conjunction:
                    case 'and':
                        result = result and r
                    case 'and not':
                        result = result and not r
                    case 'or':
                        result = result or r
                    case 'or not':
                        result = result or not r
                    case _:
                        LOG.error(
                            'do not know this conjunction %s', rule.conjunction
                        )
        return result

    @staticmethod
    def _caster(val):
        for typ in [bool, complex, float, int]:
            if isinstance(val, typ):
                return typ
        return str

    def _do_delegation(self):
        xml = self._load('categorization.xml')
        categories = dip.bindings.categorization.CreateFromDocument(xml)
        xml = self._load('system.xml')
        system = dip.bindings.system.CreateFromDocument(xml)
        archive = Path(system.archive.location)
        staging = Path(system.staging.location)
        manifest = dip.base.Manifest()
        mfn = staging / util.tn2l1mfn(self.target)
        if not mfn.is_file():
            mfn = staging / mfn.name.lower()
        if not mfn.is_file():
            raise dawgie.NoValidInputDataError(
                f'No manifest file matches target name {self.target}'
            )
        manifest.deserialize(mfn)
        shutil.move(mfn, archive / mfn.name)
        for l1 in manifest:
            l1 = Path(l1)
            channels = []
            for channelname in filter(
                lambda s: s != 'unk', self.outputs['channel']
            ):
                channel = get_tag(categories, channelname)
                if FSM._apply(channel.rule, l1):
                    channels.append(channelname)
            if channels:
                if len(channels) > 1:
                    LOG.error(
                        'L1 file %s matches more than 1 channel %s. Adding to UNK.',
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


class Operands:
    @staticmethod
    def contains_all(val, vals):
        vl = val.split(',')
        return all(v in vl for v in vals)

    @staticmethod
    def contains_any(val, vals):
        vl = val.split(',')
        return any(v in vl for v in vals)

    @staticmethod
    def equals_all(val, vals):
        return all(val == v for v in vals)

    @staticmethod
    def equals_any(val, vals):
        return any(val == v for v in vals)

'''define the hard bits of calibration'''

import dip.base
import dip.bindings.calibration
import logging

from astropy.io import fits

LOG = logging.getLogger(__name__)


class FSM(dip.base.Orchestrator):
    def _do_delegation(self):
        demux = {}
        for sv in self.inputs.values():
            for fn in sv['manifest']:
                key = _extract(fn)
                if key not in demux:
                    demux[key] = []
                demux[key].append(fn)
        template = next(iter(self.outputs.values())).__class__
        for i, fns in enumerate(demux.values()):
            consistent = template()
            consistent['manifest'].extend(fns)
            self.retargets[str(i)] = [consistent]
        return dip.base.ProductStatus.ALL


def _extract(fn):
    hdus = fits.open(fn)
    search = {'EXPTIME': None, 'EMGAIN_C': None, 'KGAINPAR': None}
    with fits.open(fn) as hdus:
        for hdu in hdus:
            for kw in search:
                if kw in hdu.header:
                    search[kw] = hdu.header[kw]
            if all(v is not None for v in search.values()):
                break
    return search['EXPTIME'], search['EMGAIN_C'], search['KGAINPAR']

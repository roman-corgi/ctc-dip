'''define the hard bits of scan'''

import dawgie.db
import dip.base
import dip.bindings.system

from pathlib import Path

from . import util


class FSM(dip.base.Orchestrator):
    def _do_delegation(self):
        xml = self._load('system.xml')
        system = dip.bindings.system.CreateFromDocument(xml)
        staging = Path(system.staging.location)
        signals = sorted(staging.glob('*.signal'))
        while signals:
            signal = signals.pop(0)
            manifest = self.outputs['inbound']['frames']
            manifest.deserialize(signal.parent / signal.stem)
            dawgie.db.add(util.l1mfn2tn(signal.name.split('.')[0]))
            signal.unlink(missing_ok=True)
        return dip.base.ProductStatus.ALL

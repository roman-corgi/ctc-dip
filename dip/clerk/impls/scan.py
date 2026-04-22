'''define the hard bits of scan'''

import dawgie.db
import dip.base
import dip.bindings.system

from pathlib import Path


class FSM(dip.base.Orchestrator):
    def _do_delegation(self):
        xml = self._load('system.xml')
        system = dip.bindings.system.CreateFromDocument(xml)
        staging = Path(system.staging.location)
        signals = sorted(staging.glob('*.signal'))
        if signals:
            signal = signals.pop(0)
            manifest = self.outputs['inbound']['frames']
            manifest.deserialize(signal.parent / signal.stem)
            c,dt = signal.name.split('.')[0].split('_')[1:3]
            d,t = dt.lower().split('t')
            dawgie.db.add(f'{c} ({d})({t})')
            signal.unlink(missing_ok=True)
        if signals:
            # pylint: disable=fixme
            # FIXME: reque self or should this be done by an external event?
            #        to do it locally here, need to call the API. Interesting.
            pass
        return dip.base.ProductStatus.ALL

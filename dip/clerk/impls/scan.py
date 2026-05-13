'''define the hard bits of scan'''

import dawgie.db
import dawgie.pl.schedule
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
        for signal in signals:
            target = util.l1mfn2tn(signal.name.split('.')[0])
            dawgie.db.add(target)
            dawgie.pl.schedule.organize(
                task_names=['clerk.categorization'],
                targets=[target],
                event=f'detected signal for {target}',
            )
            signal.unlink(missing_ok=True)
        raise dawgie.NoValidOutputDataError(
            'scan asks the scheduler to do a specific task.alg never generating output'
        )

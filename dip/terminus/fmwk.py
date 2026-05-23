"""boilerplate copied from auto generated"""

# pylint: disable=duplicate-code

import dawgie
import dawgie.util
import dip.base

from pathlib import Path


class Runnable(dawgie.Analyzer):
    def __init__(self):
        dawgie.Analyzer.__init__(self)
        self._version_ = dawgie.VERSION(1, 0, 0)

    def name(self) -> str:
        return 'est'

    def run(self, aspects: dawgie.Aspect):
        machine = dip.terminus.est.FSM()
        xml = machine._load('system.xml')  # pylint: disable=protected-access
        system = dip.bindings.system.CreateFromDocument(xml)
        staging = Path(system.staging.location) / 'custom'
        for todo in sorted(staging.glob('do*.yaml')):
            machine = dip.terminus.est.FSM()
            dip.basis.fsm.build(machine)
            machine.dawgie_name = '.'.join(repr(self).split('.')[-2:])
            machine.todo = todo
            machine.do()
            if machine.dawgie_exc is not None:
                raise machine.dawgie_exc
            if machine.panicked:
                raise dawgie.AbortAEError('we sank!')
        raise dawgie.NoValidOutputDataError(
            'manual output decapitated from automated corpus'
        )

    def state_vectors(self) -> [dawgie.StateVector]:
        return []

    def traits(self) -> [dawgie.SV_REF, dawgie.V_REF]:
        return []

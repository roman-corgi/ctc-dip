'''define the hard bits of calibration'''

import dip.base
import dip.bindings.configuration


class FSM(dip.base.Orchestrator):
    def _do_delegation(self):
        xml = self._load('configuration.xml')
        cnf = dip.bindings.configuration.CreateFromDocument(xml)
        self._fill(cnf, 'configuration.xml')
        return dip.base.ProductStatus.ALL

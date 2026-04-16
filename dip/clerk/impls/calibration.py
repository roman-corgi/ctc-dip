'''define the hard bits of calibration'''

import dip.base
import dip.bindings.calibration
import logging

LOG = logging.getLogger(__name__)


class FSM(dip.base.Orchestrator):
    def _do_delegation(self):
        xml = self._load('calibration.xml')
        cal = dip.bindings.calibration.CreateFromDocument(xml)
        self._fill(cal, 'calibration.xml')
        return dip.base.ProductStatus.ALL

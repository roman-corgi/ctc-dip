'''define the hard bits of calibration'''

import dip.base
import dip.bindings.calibration
import logging

LOG = logging.getLogger(__name__)


class FSM(dip.base.Orchestrator):
    def _do_delegation(self):
        targets = {tn.split('(')[0] for tn in self.inputs}
        targets.clear()

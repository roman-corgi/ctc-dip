'''define the hard bits of scan'''

import dawgie.context
import dawgie.db
import dip.base
import dip.bindings.system
import logging
import requests

from pathlib import Path

from . import util

LOG = logging.getLogger(__name__)


class FSM(dip.base.Orchestrator):
    def _do_delegation(self):
        xml = self._load('system.xml')
        system = dip.bindings.system.CreateFromDocument(xml)
        staging = Path(system.staging.location)
        signals = sorted(staging.glob('*.signal'))
        for signal in signals:
            target = util.l1mfn2tn(signal.name.split('.')[0])
            dawgie.db.add(target)
            resp = requests.post(
                f'{system.dip.location.rstrip('/')}/api/cmd/run',
                cert=dawgie.context.ssl_pem_myself,
                params={'runnables': 'clerk.categorization', 'targets': target},
                timeout=300,
                verify=False,
            )
            resp.raise_for_status()
            if resp.json()['status'] != 'success':
                LOG.error(
                    'request for clerk.categorization to run target %s failed because %s',
                    target,
                    resp.text,
                )
            else:
                signal.unlink(missing_ok=True)
        raise dawgie.NoValidOutputDataError(
            'scan asks the scheduler to do a specific task.alg never generating output'
        )

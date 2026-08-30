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
    def __notify(self, runnable, signal):
        resp = requests.post(
            f'{system.dip_api.location.rstrip('/')}/cmd/run',
            cert=system.dip_cid.location,
            params={'runnables': runnable, 'targets': target},
            timeout=300,
            verify=False,  # self signed certs # nosec
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

    def _do_agg(self, signal):
        target = util.vismfn2tn(signal.name.split('.')[0])
        dawgie.db.add(target)
        self.__notify('clerk.aggregation', signal)

    def _do_delegation(self):
        xml = self._load('system.xml')
        system = dip.bindings.system.CreateFromDocument(xml)
        staging = Path(system.staging.location)
        signals = sorted(staging.glob('*.signal'))
        for signal in signals:
            if signal.startswith('V'):
                self._do_agg(signal)
            elif signal.startswith('cgi_'):
                self._do_l1(signal)
            else:
                LOG.error('Unknown file type of signal: %s', signal)
        raise dawgie.NoValidOutputDataError(
            'scan asks the scheduler to do a specific task.alg never generating output'
        )

    def _do_l1(self, signal):
        target = util.l1mfn2tn(signal.name.split('.')[0])
        dawgie.db.add(target)
        self.__notify('clerk.categorization', signal)

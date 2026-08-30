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
    def __notify(self, runnable, system, target):
        resp = requests.post(
            f'{system.dip_api.location.rstrip('/')}/cmd/run',
            cert=system.dip_cid.location,
            params={'runnables': runnable, 'targets': target},
            timeout=300,
            verify=False,  # self signed certs # nosec
        )
        resp.raise_for_status()
        queued = resp.json()['status'] = 'success'
        if not queued:
            LOG.error(
                'request for %s to run target %s failed because %s',
                runnable,
                target,
                resp.text,
            )
        return queued

    def _do_agg(self, signal, system):
        target = util.vismfn2tn(signal.name.split('.')[0])
        dawgie.db.add(target)
        return self.__notify('clerk.aggregation', system, target)

    def _do_delegation(self):
        xml = self._load('system.xml')
        system = dip.bindings.system.CreateFromDocument(xml)
        staging = Path(system.staging.location)
        signals = sorted(staging.glob('*.signal'))
        for signal in signals:
            queued = False
            if signal.name.startswith('V'):
                queued = self._do_agg(signal, system)
            elif signal.name.startswith('cgi_'):
                queued = self._do_l1(signal, system)
            else:
                LOG.error('Unknown file type of signal: %s', signal)
            if queued:
                signal.unlink(missing_ok=True)
        raise dawgie.NoValidOutputDataError(
            'scan asks the scheduler to do a specific task.alg never generating output'
        )

    def _do_l1(self, signal, system):
        target = util.l1mfn2tn(signal.name.split('.')[0])
        dawgie.db.add(target)
        return self.__notify('clerk.categorization', system, target)

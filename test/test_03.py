'''test the clerks'''

'''test generic FSM transitions that they match the diagram'''

import dawgie
import dip.clerk.impls.categorization
import unittest

from dip.base import Manifest
from unittest.mock import MagicMock, patch


class AggregationClerk(unittest.TestCase):
    '''the per visit aggregation of issue #103'''

    FRAME = '0200001001001001004 (2026-09-21)(11:38:32)(0)'

    @staticmethod
    def _system():
        system = MagicMock()
        system.dip_api.location = 'https://localhost:8080/api/'
        system.dip_cid.location = '/tmp/me.pem'
        return system

    def test_jobs(self):
        '''_jobs returns the target names in the DAWGIE schedule queues

        The DAWGIE front end wraps every answer as content/message/status.
        to-do and doing answer with {task: [targets]} while in-progress
        answers with a list of "task.alg[target] duration: ..." strings.
        '''
        content = {
            'to-do': {'l1.transmutation_nfov_a': ['t1', 't2']},
            'doing': {'clerk.categorization': ['t3']},
            'in-progress': ['clerk.aggregation[t4] duration: 00:00:01'],
        }

        def answer(url, **_kwds):
            resp = MagicMock()
            resp.raise_for_status.return_value = None
            resp.json.return_value = {
                'content': content[url.split('/')[-1]],
                'message': '',
                'status': 'success',
            }
            return resp

        with patch('requests.get', side_effect=answer) as mock_get:
            jobs = dip.clerk.impls.categorization.AggFSM()._jobs(self._system())
        self.assertEqual(['t1', 't2', 't3', 't4'], jobs)
        self.assertEqual(
            [
                'https://localhost:8080/api/schedule/to-do',
                'https://localhost:8080/api/schedule/doing',
                'https://localhost:8080/api/schedule/in-progress',
            ],
            [call.args[0] for call in mock_get.call_args_list],
        )

    def test_jobs_failure(self):
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        resp.json.return_value = {
            'content': '2026-10-01 10:30:20',
            'message': 'no can do',
            'status': 'failure',
        }
        with patch('requests.get', return_value=resp):
            with self.assertRaises(ValueError) as cxt:
                dip.clerk.impls.categorization.AggFSM()._jobs(self._system())
        self.assertIn('no can do', str(cxt.exception))

    def test_max(self):
        '''only the highest level survives per target and channel

        Full names out of dawgie.db.search() are
        runid.target.task.alg.sv where task is the level and alg is
        always transmutation_<channel>.
        '''
        self.assertEqual(
            [
                f'36.{self.FRAME}.l1.transmutation_eng_a.product',
                f'36.{self.FRAME}.l2b.transmutation_nfov_pc.product',
                '36.other (2026-09-21)(11:40:00)(0).l1.'
                'transmutation_nfov_pc.product',
            ],
            dip.clerk.impls.categorization.AggFSM()._max(
                [
                    f'36.{self.FRAME}.l1.transmutation_nfov_pc.product',
                    f'36.{self.FRAME}.l2b.transmutation_nfov_pc.product',
                    f'36.{self.FRAME}.l2a.transmutation_nfov_pc.product',
                    f'36.{self.FRAME}.l1.transmutation_eng_a.product',
                    '36.other (2026-09-21)(11:40:00)(0).l1.'
                    'transmutation_nfov_pc.product',
                ]
            ),
        )

    @patch('dip.base.sv_lookup')
    @patch('dawgie.db.search')
    @patch('dawgie.db.targets')
    @patch('dip.clerk.impls.categorization.time.sleep')
    def test_collect(self, _mock_sleep, mock_targets, mock_search, mock_lookup):
        '''case 2 and case 3 of issue #103 in one visit

        nfov_pc is case 3: it has a per frame L1 product, so the product is
        what gets aggregated. cal_boresight is case 2: it has no per frame
        transmutation at all, so its raw L1 frames are the whole input set.
        '''
        product = f'36.{self.FRAME}.l1.transmutation_nfov_pc.product'
        channel = f'36.{self.FRAME}.clerk.categorization.channel'
        mock_targets.return_value = [
            self.FRAME,
            '0200001001001001004',  # the visit target itself
            'other (2026-09-21)(11:40:00)(0)',
        ]

        def find(params, *_args, **_kwds):
            return MagicMock(items=[channel, product])

        mock_search.return_value.find.side_effect = find
        mock_lookup.side_effect = {
            product: {'manifest': Manifest(['/d/nfov_pc_l2a.fits'])},
            channel: {
                'cal_boresight': Manifest(['/d/bs1.fits', '/d/bs2.fits']),
                'nfov_pc': Manifest(['/d/nfov_pc_l1.fits']),
                'eng_a': Manifest(),
                'unk': Manifest(['/d/junk.fits']),
            },
        }.__getitem__

        agg = dip.clerk.impls.categorization.AggFSM()
        agg._jobs = MagicMock(return_value=[])
        collection = agg._collect(
            self._system(), Manifest(['0200001001001001004'])
        )

        self.assertEqual(
            ['/d/bs1.fits', '/d/bs2.fits', '/d/nfov_pc_l2a.fits'],
            sorted(collection),
        )
        self.assertNotIn('/d/nfov_pc_l1.fits', collection)
        self.assertNotIn('/d/junk.fits', collection)

    @patch('dip.base.sv_lookup')
    @patch('dawgie.db.search')
    @patch('dawgie.db.targets')
    @patch('dip.clerk.impls.categorization.time.sleep')
    def test_collect_boresight_only(
        self, _mock_sleep, mock_targets, mock_search, mock_lookup
    ):
        '''a CGIVST_CAL_BORESIGHT visit, which is pure case 2

        Every frame lands in cal_boresight and nothing below
        l1.transmutation_cal_boresight exists, so the visit has no product
        state vector at all. The raw L1 frames still have to be aggregated.
        '''
        channel = f'36.{self.FRAME}.clerk.categorization.channel'
        frames = [f'/d/cgi_{i}_l1_.fits' for i in range(27)]
        mock_targets.return_value = [self.FRAME, '0200001001001001004']
        mock_search.return_value.find.side_effect = (
            lambda params, *_a, **_k: MagicMock(
                items=[] if params.svs == ['product'] else [channel]
            )
        )
        mock_lookup.return_value = {
            'cal_boresight': Manifest(frames),
            'nfov_a': Manifest(),
            'unk': Manifest(),
        }

        agg = dip.clerk.impls.categorization.AggFSM()
        agg._jobs = MagicMock(return_value=[])
        collection = agg._collect(
            self._system(), Manifest(['0200001001001001004'])
        )

        self.assertEqual(sorted(frames), list(collection))

'''test the clerks'''

'''test generic FSM transitions that they match the diagram'''

import dawgie
import dip.bindings
import dip.clerk.auto.calibration
import dip.clerk.auto.categorization
import dip.clerk.auto.configuration
import dip.clerk.auto.recipe
import dip.clerk.impls.calibration
import dip.clerk.impls.categorization
import dip.clerk.impls.config
import dip.clerk.impls.recipe
import dip.clerk.impls.scan
import dip.clerk.impls.util
import numpy
import tempfile
import unittest
import yaml

from astropy.io import fits
from dip.base import Manifest, ProductStatus
from pathlib import Path
from unittest.mock import MagicMock, patch


class BasicClerks(unittest.TestCase):
    def test_calibration(self):
        cal = dip.clerk.impls.calibration.FSM()
        cal.outputs.update(dip.clerk.auto.calibration.Runnable().sv_as_dict())
        cal._do_delegation()

    def test_categorization(self):
        with tempfile.TemporaryDirectory() as workspace:
            cat = dip.clerk.impls.categorization.FrameFSM()
            cat.features = {'clerk.scan.inbound': ['frames']}
            cat.inputs = {'clerk.scan.inbound': {'frames': []}}
            cat.outputs.update(
                dip.clerk.auto.categorization.Runnable().sv_as_dict()
            )
            dummy_data = numpy.zeros((10, 10), dtype=numpy.int16)
            expectation = {
                'channel': dip.clerk.auto.categorization.ChannelStateVector()
            }
            workspace = Path(workspace)
            for info in [
                {
                    'filename': 'cgi_11_a_l1_.fits',
                    'vistype': 'banana',
                    'aq': 10,
                },
                {'filename': 'cgi_12_a_l1_.fits', 'vistype': 'apple', 'aq': 4},
                {'filename': 'cgi_13_a_l1_.fits', 'vistype': 'cherry', 'aq': 0},
                {
                    'filename': 'cgi_14_a_l1_.fits',
                    'vistype': 'orange',
                    'aq': 15,
                },
            ]:
                hdu = fits.PrimaryHDU(data=dummy_data)
                hdu.header['VISTYPE'] = info['vistype']
                hdu.header['AQ'] = info['aq']
                fn = workspace / info['filename']
                hdu.writeto(fn)
                cat.inputs['clerk.scan.inbound']['frames'].append(str(fn))
                n = int(info['filename'].split('_')[1])
                if n > 12:
                    expectation['channel']['unk'].append(fn)
                else:
                    expectation['channel']['eng_a'].append(fn)
            print(cat.inputs)
            cat.target = 'apple (cherry)(grape)(plum)'
            with open(
                Path(__file__).parent.parent
                / 'dip'
                / 'base'
                / 'categorization.xml',
                'rt',
            ) as file:
                rules = dip.bindings.categorization.CreateFromDocument(
                    file.read()
                )
            cat._collate(rules, cat.inputs['clerk.scan.inbound']['frames'])
            self.assertEqual(expectation, cat.outputs)

    def test_configuration(self):
        cnf = dip.clerk.impls.calibration.FSM()
        cnf.outputs.update(dip.clerk.auto.configuration.Runnable().sv_as_dict())
        cnf._do_delegation()

    def test_recipe(self):
        rec = dip.clerk.impls.calibration.FSM()
        rec.outputs.update(dip.clerk.auto.recipe.Runnable().sv_as_dict())
        rec._do_delegation()

    @patch('dawgie.db.add')
    @patch('requests.post')
    def test_scan(self, mock_post, mock_add):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "data": "payload",
        }
        mock_response.text = '{"status": "success", "data": "payload"}'
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        with tempfile.TemporaryDirectory() as workspace:
            workspace = Path(workspace)
            scan = dip.clerk.impls.scan.FSM()
            scan.outputs['inbound'] = {}
            scan.outputs['inbound']['frames'] = Manifest()
            scan._load = MagicMock(return_value=f'''
<system>
  <archive location="{workspace}"/>
  <dip_api location="https://localhost:8080/api"/>
  <dip_cid location="{workspace}/me.cert"/>
  <journal location="{workspace}"/>
  <panics location="{workspace}"/>
  <staging location="{workspace}"/>
</system>
        '''.encode())

            with self.assertRaises(dawgie.NoValidOutputDataError) as cxt:
                scan._do_delegation()
            self.assertEqual(0, len(scan.outputs['inbound']['frames']))
            fn = workspace / 'cgi_blahblah_YYYYMMDDtHHMMSS_l1_.manifest'
            manifest = ['/a/b/c/l1.1', '/a/b/c/l1.2', '/a/b/c/l1.3']
            fn.write_text(yaml.dump(manifest))
            with self.assertRaises(dawgie.NoValidOutputDataError) as cxt:
                scan._do_delegation()
            self.assertEqual(0, len(scan.outputs['inbound']['frames']))
            fn = fn.with_name(fn.name + '.signal')
            fn.touch()
            with self.assertRaises(dawgie.NoValidOutputDataError) as cxt:
                scan._do_delegation()
            self.assertEqual([], scan.outputs['inbound']['frames'])

    def test_util(self):
        mfn = 'cgi_0200001001001001001_20260415T1655330_l1_.yaml'
        self.assertEqual(
            mfn,
            dip.clerk.impls.util.tn2l1mfn(dip.clerk.impls.util.l1mfn2tn(mfn)),
        )


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
            if params.svs == ['product']:
                self.assertEqual({self.FRAME}, params.targets)
                return MagicMock(items=[product])
            self.assertEqual(['channel'], params.svs)
            # clerk.aggregation owns a state vector called channel too, so
            # the search has to name the categorization explicitly
            self.assertEqual(['clerk'], params.tasks)
            self.assertEqual(['categorization'], params.algs)
            return MagicMock(items=[channel])

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

        self.assertEqual(frames, list(collection))

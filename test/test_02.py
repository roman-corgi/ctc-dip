'''test the clerks'''

'''test generic FSM transitions that they match the diagram'''

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
from dip.base import Manifest
from pathlib import Path
from unittest.mock import MagicMock, patch


class BasicClerks(unittest.TestCase):
    def test_calibration(self):
        cal = dip.clerk.impls.calibration.FSM()
        cal.outputs.update(dip.clerk.auto.calibration.Runnable().sv_as_dict())
        cal._do_delegation()

    def test_categorization(self):
        with tempfile.TemporaryDirectory() as workspace:
            cat = dip.clerk.impls.categorization.FSM()
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
            cat._do_delegation()
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
    def test_scan(self, mock_add):
        with tempfile.TemporaryDirectory() as workspace:
            workspace = Path(workspace)
            scan = dip.clerk.impls.scan.FSM()
            scan.outputs['inbound'] = {}
            scan.outputs['inbound']['frames'] = Manifest()
            scan._load = MagicMock(return_value=f'''
<system>
  <archive location='{workspace}'/>
  <staging location='{workspace}'/>
</system>
        '''.encode())
            scan._do_delegation()
            self.assertEqual(0, len(scan.outputs['inbound']['frames']))
            fn = workspace / 'cgi_blahblah_YYYYMMDDtHHMMSS_l1_.manifest'
            manifest = ['/a/b/c/l1.1', '/a/b/c/l1.2', '/a/b/c/l1.3']
            fn.write_text(yaml.dump(manifest))
            scan._do_delegation()
            self.assertEqual(0, len(scan.outputs['inbound']['frames']))
            fn = fn.with_name(fn.name + '.signal')
            fn.touch()
            scan._do_delegation()
            self.assertEqual(manifest, scan.outputs['inbound']['frames'])

    def test_util(self):
        mfn = 'cgi_0200001001001001001_20260415T1655330_l1_.yaml'
        self.assertEqual(
            mfn,
            dip.clerk.impls.util.tn2l1mfn(dip.clerk.impls.util.l1mfn2tn(mfn)),
        )

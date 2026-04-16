'''Data Integration Processor (DIP) base elements'''

import corgidrp.ops
import dawgie
import dip.basis.fsm
import logging
import os
import shutil

from datetime import UTC, datetime
from dip.binding_help import get_tag
from importlib import resources
from pathlib import Path
from tempfile import TemporaryDirectory

from ._types import (
    Calibration,
    Configuration,
    Contaminable,
    Cpgs,
    Manifest,
    Recipe,
)

LOG = logging.getLogger(__name__)


class Orchestrator(dip.basis.fsm.AbstractModel):
    def _do_construction(self) -> bool:
        return True

    def _do_general_quarters(self) -> dip.basis.fsm.AlertStatus:
        return dip.basis.fsm.AlertStatus.FOUNDERED

    def _do_sanitization(self):
        pass

    def _do_warehouse(self) -> bool:
        return True

    def _fill(self, bound_xml, fn):
        for sv in self.outputs.values():
            svn = sv.name()
            for valname, val in sv.items():
                name = f'{svn}.{valname}'
                item = get_tag(bound_xml, name)
                if item is None:
                    LOG.error('Could not find tag %s in %s', name, fn)
                else:
                    val.name = Path(item.location) if item.location else None

    def _load(self, xmlname) -> bytes:
        return _load_xml(xmlname)


class Runner(dip.basis.fsm.AbstractModel):
    def __init__(self):
        dip.basis.fsm.AbstractModel.__init__(self)
        self.__caldir: Path = None
        self.__cpgs: Path = None
        self.__log = LOG.getChild(self.__class__.__name__)
        self.__manifest: Manifest = None
        self.__outdir: Path = None
        self.__sandbox: TemporaryDirectory = None
        self.__template: Path = None

    def __update(self, val, name):
        if isinstance(val, Cpgs):
            self.__log.info('Found %s to be CPGS', name)
            if self.__cpgs is None:
                self.__cpgs = val.name
            else:
                self.__log.error(
                    'Found more than one CPGS! First come first used.'
                )
        if isinstance(val, Manifest):
            self.__log.info('Found %s to be Manifest', name)
            if self.__manifest is None:
                self.__manifest = val
            else:
                self.__log.error(
                    'Found more than one manifest! First come first used.'
                )
        if isinstance(val, Recipe):
            self.__log.info('Found %s to be Recipe', name)
            if self.__template is None:
                self.__template = val.name
            else:
                self.__log.error(
                    'Found more than one recipe! First come first used.'
                )

    def _do_construction(self) -> bool:
        '''do the construnction state

        Return true if all went well. Other false or throw an exception, which
        will be logged.
        '''
        success = True
        try:  # pylint: disable=consider-using-with
            # just create it because the FSM always calls sanitzation()
            self.__sandbox = TemporaryDirectory()
            location = Path(self.__sandbox.name)
            self.__caldir = location / 'caldata'
            self.__outdir = location / 'output'
            self.__caldir.mkdir(parents=True, exist_ok=True)
            self.__outdir.mkdir(parents=True, exist_ok=True)
            self.__log.info('inputs: %s', str(self.inputs))
            for svn, sv in self.inputs.items():
                for name in self.features[svn]:
                    val = sv[name]
                    if not isinstance(val, Contaminable):
                        continue
                    locale = (
                        self.__caldir
                        if isinstance(val, Calibration)
                        else location
                    )
                    sv[name] = val.quarantine(locale)
                    self.__update(val, f'{svn}.{name}')
        except:  # noqa; 722 # pylint: disable=bare-except
            self.__log.exception('Cound not create a sanbox')
            success = False
        return success

    def _do_delegation(self) -> dip.basis.fsm.ProductStatus:
        '''run the DRP via corgidrp.ops'''
        if not self.__manifest:
            raise dawgie.NoValidInputDataError('input manifest is empty')
        self.__log.info('doing step 1: initialize')
        ctxt = corgidrp.ops.step_1_initialize()
        LOG.info('doing step 2: load cal: %s', self.__caldir)
        corgidrp.ops.step_2_load_cal(
            this_caldb=ctxt, main_cal_dir=self.__caldir
        )
        self.__log.info(
            'doing step 3: process data: %d, %s, %s, %s',
            len(self.__manifest),
            self.__cpgs,
            self.__outdir,
            self.__template,
        )
        corgidrp.ops.step_3_process_data(
            input_filelist=list(str(fn) for fn in self.__manifest),
            cpgs_xml_filepath=str(self.__cpgs) if self.__cpgs else None,
            outputdir=str(self.__outdir),
            template=str(self.__template) if self.__template else None,
        )
        self.__log.info('done processing')
        # FIXME: test for product files that are needed # pylint: disable=fixme
        return dip.basis.fsm.ProductStatus.ALL

    def _do_general_quarters(self) -> dip.basis.fsm.AlertStatus:
        '''Called by do_general_quarters()

        do_general_quarters() has already secured all of the logs and prepared
        them for the next step. This function determines what to do with
        information that has been prepared.
        '''
        return dip.basis.fsm.AlertStatus.FOUNDERED

    def _do_sanitization(self):
        if self.__sandbox:
            self.__sandbox.cleanup()
            self.__sandbox = None

    def _do_warehouse(self) -> bool:
        '''move the data to SSC storage location'''
        self.outputs['product']['manifest'] = Manifest()
        dst = None
        name = None
        for sv in self.inputs.values():
            if 'outdir' in sv and isinstance(sv['outdir'], Configuration):
                if dst is not None:
                    self.__log.error(
                        'More than one output destination was given'
                    )
                    return False
                dst = str(sv['outdir'].name)
        if dst is None:
            self.__log.error(
                'No dip.base.Configuration output destinations were given'
            )
            return False
        now = datetime.now(UTC).isoformat(sep='t', timespec='seconds')[:-6]
        now = now.replace('-', '').replace(':', '')
        for fn in os.listdir(self.__outdir):
            vid = _dissect(str(fn))
            dstdir = Path(dst.format(now=now, **vid))
            dstdir.mkdir(parents=True, exist_ok=True)
            dstfn = dstdir / fn
            shutil.copy(self.__outdir / fn, dstfn)
            if dstfn.suffix == '.fits':
                self.outputs['product']['manifest'].append(dstfn.resolve())
                name = dstfn.stem
        if name:
            arc = Path(
                dip.bindings.system.CreateFromDocument(
                    _load_xml('system.xml')
                ).archive.location
            )
            manifest = arc / (name + '.yaml')
            self.outputs['product']['manifest'].serialize(manifest)
            manifest.with_name(manifest.name + '.signal').touch()
        return True


def _dissect(fn: str) -> {}:
    '''break the visit id apart from the file name'''
    vid = fn.split('_')[1]
    return {
        'p': vid[:5],
        'c': vid[5:7],
        'a': vid[7:10],
        's': vid[10:13],
        'o': vid[13:16],
        'v': vid[16:],
    }


def _load_xml(xmlname) -> bytes:
    '''return the path to the resource location'''
    fn = Path('/proj/dip/etc') / xmlname
    if not fn.is_file():
        fn = resources.files('dip.base') / xmlname
    return fn.read_bytes()

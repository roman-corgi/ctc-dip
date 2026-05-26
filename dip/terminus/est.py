'''define the hard bits of scan'''

# pylint: disable=duplicate-code

import corgidrp.ops
import dip.base
import dip.bindings.system
import logging
import os
import shutil
import yaml

from pathlib import Path
from tempfile import TemporaryDirectory

LOG = logging.getLogger(__name__)


class FSM(dip.base.Orchestrator):
    def __init__(self):
        super().__init__()
        self.__caldir = None
        self.__cpgs = None
        self.__manifest = None
        self.__outdir = None
        self.__template = None
        self.__sandbox = None
        self._todo = None

    @property
    def todo(self):
        return self._todo

    @todo.setter
    def todo(self, p: Path):
        self._todo = p

    def _do_construction(self) -> bool:
        '''do the construnction state

        Return true if all went well. Other false or throw an exception, which
        will be logged.
        '''
        success = True
        try:  # pylint: disable=consider-using-with
            # just create it because the FSM always calls sanitzation()
            do = yaml.safe_load(self._todo.read_text(encoding='utf-8'))
            for k, t in [
                ('cal_manifest', True),
                ('l1_manifest', True),
                ('outdir', False),
                ('recipe', True),
            ]:
                do[k] = _check(k, do[k], t)
            self.__sandbox = TemporaryDirectory()
            location = Path(self.__sandbox.name)
            self.__caldir = location / 'caldata'
            self.__outdir = do['outdir']
            self.__template = do['recipe']
            self.__caldir.mkdir(parents=True, exist_ok=True)
            self.__outdir.mkdir(parents=True, exist_ok=True)
            m = dip.base.Manifest()
            mp = dip.base.Manifest()
            m.deserialize(do['l1_manifest'])
            mp.extend(Path(p) for p in m)
            self.__manifest = mp.quarantine(location)
            m.deserialize(do['cal_manifest'])
            mp.extend(Path(p) for p in m)
            mp.quarantine(self.__caldir)
        except:  # noqa; 722 # pylint: disable=bare-except
            self.__log.exception('Cound not create a sanbox')
            success = False
        return success

    def _do_delegation(self):
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
        return dip.basis.fsm.ProductStatus.ALL

    def _do_sanitization(self):
        if self.__sandbox:
            self.__sandbox.cleanup()
            self.__sandbox = None
            caldb = Path(os.path.expandvars('${HOME}/.corgidrp'))
            if caldb.is_dir():
                for item in caldb.iterdir():
                    if item.is_dir() and not item.is_symlink():
                        shutil.rmtree(item)
                    else:
                        item.unlink()


def _check(key: str, path: str, isfile: bool = True) -> Path:
    p = Path(path)
    if isfile and not p.is_file():
        raise ValueError(f'the key {key} value {path} is not a file')
    if not isfile and p.exists() and not p.is_dir():
        raise ValueError(f'the key {key} value {path} is not a directory')
    return p
